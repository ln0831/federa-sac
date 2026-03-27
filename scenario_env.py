"""scenario_env.py

Scenario wrapper for DistNetEnv.

This wrapper adds *time-varying disturbances* on top of the existing
pandapower-based distribution network environments.

It supports A/B/C experiments:

- A (tidal/QSTS): periodic load + PV-availability changes.
- B (topology outages): handled by env itself via topology_mode=random_reset.
- C (combined): topology outages + tidal + a localized step load disturbance.

The wrapper works by capturing the baseline injections after env.reset(),
then applying per-step scalings directly to env.net before calling env.step().

Usage pattern (in train/test scripts):

    from scenario_env import DisturbanceConfig, ScenarioWrapper
    cfg = DisturbanceConfig(mode='tidal', tidal_period=96, ...)
    env = ScenarioWrapper(env, cfg)

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

try:
    import pandapower as pp
except Exception:  # pragma: no cover
    pp = None  # type: ignore


def _sin_scale(t: int, period: int, base: float, amp: float, phase: float = 0.0) -> float:
    """Sinusoidal scale: base + amp * sin(2π t / period + phase)."""
    if period <= 0:
        return float(base)
    val = float(base) + float(amp) * float(np.sin(2.0 * np.pi * float(t) / float(period) + float(phase)))
    # prevent negative scaling
    return float(max(0.0, val))


@dataclass
class DisturbanceConfig:
    # none | tidal | step | tidal_step
    mode: str = "none"

    # tidal
    tidal_period: int = 96
    tidal_load_base: float = 1.0
    tidal_load_amp: float = 0.2
    tidal_pv_base: float = 1.0
    tidal_pv_amp: float = 0.5
    tidal_phase: float = 0.0

    # step
    step_t: int = 24
    step_factor: float = 1.2
    step_target: str = "random_agent"  # all | random_agent | agent0..agent3

    # misc
    dist_seed: int = 0
    reset_load_mode: str = "keep"  # keep | base  (base will override env.reset random load jitter)
    recompute_on_reset: bool = True


class ScenarioWrapper:
    """Wrap an env to inject disturbances."""

    def __init__(self, env, cfg: DisturbanceConfig):
        self.env = env
        self.cfg = cfg
        self.t = 0
        self._base_load_p: Optional[np.ndarray] = None
        self._base_load_q: Optional[np.ndarray] = None
        self._base_sgen_sn: Optional[np.ndarray] = None
        self._step_load_mask: Optional[np.ndarray] = None

    def __getattr__(self, name):
        return getattr(self.env, name)

    def _episode_index(self) -> int:
        # env_*.py uses env.episode_idx incremented at end of reset
        if hasattr(self.env, "episode_idx"):
            try:
                return int(getattr(self.env, "episode_idx")) - 1
            except Exception:
                pass
        return 0

    def _choose_step_mask(self) -> Optional[np.ndarray]:
        if not (hasattr(self.env, "net") and hasattr(self.env.net, "load") and len(self.env.net.load) > 0):
            return None
        mode = str(self.cfg.mode).lower()
        if "step" not in mode:
            return None

        load_buses = self.env.net.load.bus.values
        if str(self.cfg.step_target).lower() == "all":
            return np.ones(len(load_buses), dtype=bool)

        # Map step_target to agent index
        num_agents = int(getattr(self.env, "num_agents", 1))
        ep = self._episode_index()
        rng = np.random.default_rng(int(self.cfg.dist_seed) + int(ep))

        target = str(self.cfg.step_target).lower()
        if target == "random_agent":
            agent_i = int(rng.integers(0, max(1, num_agents)))
        elif target.startswith("agent") and target[5:].isdigit():
            agent_i = int(target[5:])
        else:
            agent_i = 0

        agent_i = int(np.clip(agent_i, 0, max(0, num_agents - 1)))

        if hasattr(self.env, "areas") and self.env.areas is not None:
            try:
                buses = np.array(self.env.areas[agent_i], dtype=int)
                return np.isin(load_buses.astype(int), buses)
            except Exception:
                pass

        # fallback: apply to all loads
        return np.ones(len(load_buses), dtype=bool)

    def _capture_base(self) -> None:
        # capture baseline injections after reset (and optional de-randomization)
        if hasattr(self.env, "net") and hasattr(self.env.net, "load") and len(self.env.net.load) > 0:
            self._base_load_p = self.env.net.load.p_mw.values.copy()
            self._base_load_q = self.env.net.load.q_mvar.values.copy()
        else:
            self._base_load_p = None
            self._base_load_q = None

        if hasattr(self.env, "net") and hasattr(self.env.net, "sgen") and len(self.env.net.sgen) > 0:
            if "sn_mva" in self.env.net.sgen.columns:
                self._base_sgen_sn = self.env.net.sgen.sn_mva.values.copy()
            else:
                self._base_sgen_sn = None
        else:
            self._base_sgen_sn = None

    def _restore_base_loads(self) -> None:
        # optional: remove reset-time load noise for deterministic scenario runs
        if str(self.cfg.reset_load_mode).lower() != "base":
            return
        if not (hasattr(self.env, "initial_load_p") and hasattr(self.env, "initial_load_q")):
            return
        if hasattr(self.env, "net") and hasattr(self.env.net, "load") and len(self.env.net.load) > 0:
            try:
                p0 = np.asarray(self.env.initial_load_p)
                q0 = np.asarray(self.env.initial_load_q)
                if len(p0) == len(self.env.net.load):
                    self.env.net.load.p_mw[:] = p0
                    self.env.net.load.q_mvar[:] = q0
            except Exception:
                pass

    def _apply_disturbance(self, t: int) -> Tuple[float, float, bool]:
        """Apply disturbance for step t.

        Returns:
            (load_scale, pv_scale, step_active)
        """
        mode = str(self.cfg.mode).lower()
        load_scale = 1.0
        pv_scale = 1.0
        step_active = False

        if "tidal" in mode:
            load_scale = _sin_scale(t, self.cfg.tidal_period, self.cfg.tidal_load_base, self.cfg.tidal_load_amp, self.cfg.tidal_phase)
            pv_scale = _sin_scale(t, self.cfg.tidal_period, self.cfg.tidal_pv_base, self.cfg.tidal_pv_amp, self.cfg.tidal_phase)

        # apply load scaling first
        if self._base_load_p is not None and hasattr(self.env, "net") and hasattr(self.env.net, "load") and len(self.env.net.load) > 0:
            self.env.net.load.p_mw[:] = self._base_load_p * load_scale
            self.env.net.load.q_mvar[:] = self._base_load_q * load_scale

        # apply step change on top
        if "step" in mode and (self._step_load_mask is not None) and int(t) >= int(self.cfg.step_t):
            step_active = True
            try:
                mask = self._step_load_mask
                self.env.net.load.p_mw.values[mask] *= float(self.cfg.step_factor)
                self.env.net.load.q_mvar.values[mask] *= float(self.cfg.step_factor)
            except Exception:
                pass

        # PV availability scaling via sn_mva
        if self._base_sgen_sn is not None and hasattr(self.env, "net") and hasattr(self.env.net, "sgen") and len(self.env.net.sgen) > 0:
            try:
                sn = self._base_sgen_sn * pv_scale
                sn = np.clip(sn, 1e-6, None)
                self.env.net.sgen.sn_mva[:] = sn
            except Exception:
                pass

        return float(load_scale), float(pv_scale), bool(step_active)

    def reset(self):
        obs = self.env.reset()
        self.t = 0

        # optional: deterministic base loads
        self._restore_base_loads()

        # capture baseline after reset (or after de-randomization)
        self._capture_base()

        # choose step target mask per-episode (deterministic via dist_seed + episode)
        self._step_load_mask = self._choose_step_mask()

        # apply disturbances at t=0 and (optionally) recompute PF so obs is consistent
        if str(self.cfg.mode).lower() != "none":
            self._apply_disturbance(0)
            if self.cfg.recompute_on_reset and pp is not None and hasattr(self.env, "net"):
                try:
                    pp.runpp(self.env.net, numba=False)
                    # env uses success flag
                    if hasattr(self.env, "success"):
                        ok = bool(getattr(self.env.net, "converged", False))
                        setattr(self.env, "success", ok)
                except Exception:
                    if hasattr(self.env, "success"):
                        setattr(self.env, "success", False)

            # return fresh obs
            if hasattr(self.env, "_get_obs"):
                return self.env._get_obs()

        return obs

    def step(self, actions):
        if str(self.cfg.mode).lower() != "none":
            load_scale, pv_scale, step_active = self._apply_disturbance(self.t)
        else:
            load_scale, pv_scale, step_active = 1.0, 1.0, False

        next_obs, rewards, done, info = self.env.step(actions)

        # attach disturbance metadata
        if isinstance(info, dict):
            info.setdefault("disturbance_mode", str(self.cfg.mode).lower())
            info.setdefault("dist_t", int(self.t))
            info.setdefault("load_scale", float(load_scale))
            info.setdefault("pv_scale", float(pv_scale))
            info.setdefault("step_active", bool(step_active))
            info.setdefault("step_target", str(self.cfg.step_target))

        self.t += 1
        return next_obs, rewards, done, info
