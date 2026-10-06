"""Actuator sizing and air consumption for the pneumatic bar-bending machine.

Reproduces the sizing calculations of the project:
  * rotary actuators (B: vertical bends, E: horizontal bend) from the bending
    moment needed to yield the copper bar;
  * linear cylinders (A: feed, C: lift, D: clamp) from the force they must deliver;
  * air consumption per cycle of every actuator and of the whole circuit.

Run:  python sizing/actuator_sizing.py
"""
from math import pi, sqrt

P = 6.0            # supply pressure [bar] (gauge)
P_ABS = P + 1.0    # absolute pressure used for air consumption [bar]
LOAD_RATIO = 0.7   # design load ratio R (required / available)
FRICTION = 0.15    # internal friction losses -> useful = 0.85 * theoretical
G = 9.81

# Copper bar
WIDTH, THICK = 30.0, 5.0     # [mm]
SIGMA_Y = 70.0               # yield strength of copper [MPa = N/mm^2]


def rotary(name, W):
    """Bending moment -> theoretical torque required from the actuator."""
    m_res = SIGMA_Y * W / 1000            # moment that yields the bar [Nm]
    m_req = m_res / LOAD_RATIO
    m_theo = m_req / (1 - FRICTION)
    print(f"{name}: W = {W:.0f} mm^3, M_res = {m_res:.2f} Nm, "
          f"M_required = {m_req:.2f} Nm, M_theoretical = {m_theo:.2f} Nm")
    return m_theo


def linear(name, f_load=None, f_req=None):
    """Load force (or directly the required force) -> theoretical force -> minimum bore."""
    if f_req is None:
        f_req = f_load / LOAD_RATIO
    f_theo = f_req / (1 - FRICTION)
    d_min = sqrt(40 * f_theo / (P * pi))   # F[N] = pi d^2[mm^2] p[bar] / 40
    load = f"F_load = {f_load:.2f} N, " if f_load is not None else ""
    print(f"{name}: {load}F_required = {f_req:.2f} N, "
          f"F_theoretical = {f_theo:.2f} N, minimum bore = {d_min:.2f} mm")
    return d_min


def air_linear(d, ds, stroke_cm):
    """Free-air consumption of a double-acting cylinder per cycle [dm^3]."""
    qs = pi / 4 * d**2 * 10 * P_ABS * 1e-6              # extension, per cm of stroke
    qt = pi / 4 * (d**2 - ds**2) * 10 * P_ABS * 1e-6    # retraction, per cm of stroke
    return (qs + qt) * stroke_cm


def air_rotary(bore, stroke_cm):
    """Rack-and-pinion actuator approximated as 2 double-acting cylinders."""
    return 4 * pi / 4 * bore**2 * 10 * P_ABS * 1e-6 * stroke_cm


print("--- Rotary actuators")
mB = rotary("B (vertical bend)", WIDTH * THICK**2 / 6)      # bending about the thin side
mE = rotary("E (horizontal bend)", WIDTH**2 * THICK / 6)    # bending about the wide side
print(f"  -> Festo DRRD-35-180-FH-PA: 15.8 Nm at 6 bar  >= {mB:.2f} Nm")
print(f"  -> Festo DRRD-63-180-FH-PA: 112 Nm at 6 bar   >= {mE:.2f} Nm")

print("\n--- Linear cylinders")
linear("A (feed, moves 4.5 kg unit)", 4.5 * G)
linear("C (lift, moves 6.5 kg unit)", 6.5 * G)
linear("D (clamp on the bar)", f_req=80.0)
print("  -> Festo DSNU-16 (bore 16 mm, rod 8 mm): A stroke 50 mm, C and D stroke 60 mm")

print("\n--- Air consumption per cycle [dm^3]")
air = {
    "A  DSNU-16-50": air_linear(16, 8, 5),
    "B  DRRD-35":    air_rotary(35, 5),
    "C  DSNU-16-60": air_linear(16, 8, 6),
    "D  DSNU-16-60": air_linear(16, 8, 6),
    "E  DRRD-63":    air_rotary(63, 5),
}
for k, v in air.items():
    print(f"  {k:15s} {v:6.3f}")
print(f"  {'Total':15s} {sum(air.values()):6.3f}   (project value: 6.124, with rounded intermediate terms)")
