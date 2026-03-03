# Electric Vehicle Digital Twin - Comprehensive Function Documentation

## Table of Contents
1. [Battery Models](#1-battery-models)
   - [SimplifiedBatteryModel](#11-simplifiedbatterymodel)
   - [EnhancedBatteryModel](#12-enhancedbatterymodel)
   - [BatteryDFNModel](#13-batterydfnmodel)
2. [Motor Models](#2-motor-models)
   - [SimplifiedPMSMMotorModel](#21-simplifiedpmsmmotormodel)
   - [EnhancedPMSMMotorModel](#22-enhancedpmsmmotormodel)
   - [PMSMMotorModel](#23-pmsmmotormodel)
3. [Integration Layer](#3-integration-layer)
   - [ElectricVehicleDigitalTwin](#31-electricvehicledigitaltwin)
   - [EnhancedElectricVehicleDigitalTwin](#32-enhancedelectricvehicledigitaltwin)
4. [Simulation Interfaces](#4-simulation-interfaces)
   - [RealTimeEVSimulation](#41-realtimeevsimulation)
   - [EVReportingDashboard](#42-evreportingdashboard)
5. [Launcher Utilities](#5-launcher-utilities)

---

## 1. Battery Models

### 1.1 SimplifiedBatteryModel

**Location:** `ev_digital_twin/battery_model/simplified_battery_model.py`

A physics-based lithium-ion battery simulation model using ordinary differential equations (ODEs) solved via SciPy's `solve_ivp`.

---

#### `__init__(self, initial_soc=1.0, capacity=3.4, nominal_voltage=3.7)`

**Purpose:** Initializes the battery model with configurable parameters and establishes physical constants.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `initial_soc` | float | 1.0 | Initial state of charge (0.0 = empty, 1.0 = full) |
| `capacity` | float | 3.4 | Battery capacity in Ampere-hours (Ah) |
| `nominal_voltage` | float | 3.7 | Nominal voltage in Volts (V) |

**Internal Constants Set:**
- `r_internal = 0.05`: Internal resistance (Ω) - affects voltage drop and heat generation
- `thermal_mass = 1200.0`: Thermal mass (J/K) - determines temperature response time
- `cooling_coefficient = 10.0`: Cooling coefficient (W/K) - heat dissipation rate
- `ambient_temp = 298.15`: Ambient temperature (K) - 25°C reference
- `max_temp = 333.15`: Maximum safe temperature (K) - 60°C threshold
- `k_voltage = 0.1`: Voltage-SOC curve steepness for linear region
- `v_full`: Voltage at full charge = nominal + 0.5V
- `v_empty`: Voltage at empty = nominal - 0.7V

**How It Works:**
The constructor establishes the battery's electrochemical and thermal characteristics. The voltage model uses a piecewise function: exponential curves at high (>90%) and low (<10%) SOC regions with a linear approximation in between. This mimics real lithium-ion behavior where voltage changes rapidly near charge limits.

---

#### `_calculate_voltage(self, soc)`

**Purpose:** Computes terminal voltage based on state of charge using a nonlinear piecewise model.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `soc` | float | State of charge (0.0 to 1.0) |

**Returns:** `float` - Battery voltage in Volts

**Algorithm:**
```
if soc >= 0.9:
    # High SOC: Exponential rise (charge acceptance decreases)
    V = V_full - (V_full - V_nominal) * exp(-10 * (soc - 0.9))
elif soc <= 0.1:
    # Low SOC: Exponential drop (depletion curve)
    V = V_empty + (V_nominal - V_empty) * exp(10 * soc)
else:
    # Linear region (10-90% SOC): V = V_nominal + (soc - 0.5) * k
```

**Technical Details:**
The exponential coefficients (±10) control the curvature steepness at charge boundaries. This models the Butler-Volmer kinetics where electrode reactions become mass-transport limited at extreme SOC values.

---

#### `_battery_dynamics(self, t, state, current)`

**Purpose:** Defines the ODE system governing battery state evolution for numerical integration.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `t` | float | Time variable (required by ODE solver) |
| `state` | array | Current state vector [SOC, Temperature] |
| `current` | float | Applied current in Amperes (positive = discharge) |

**Returns:** `array` - State derivatives [dSOC/dt, dTemp/dt]

**ODE System:**

**1. SOC Dynamics (Coulomb Counting):**
```python
dSOC/dt = -I / (capacity * 3600)
```
- Division by 3600 converts Ah to As (coulombs)
- Negative sign: positive current depletes charge

**2. Temperature Dynamics (Thermal Balance):**
```python
Q_generated = I² * R_internal    # Joule heating (W)
Q_cooling = k_cool * (T - T_ambient)  # Newton's law of cooling (W)
dT/dt = (Q_generated - Q_cooling) / thermal_mass
```

**Physical Interpretation:**
The thermal model balances resistive heat generation (I²R losses) against convective cooling. The `thermal_mass` creates a first-order lag, simulating the battery's thermal inertia - larger packs respond slower to temperature changes.

---

#### `simulate(self, current_profile, duration, dt=1.0)`

**Purpose:** Executes time-domain simulation with arbitrary current input using Runge-Kutta integration.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `current_profile` | callable | - | Function `f(t) -> current` returning current at time t |
| `duration` | float | - | Simulation duration in seconds |
| `dt` | float | 1.0 | Output time resolution in seconds |

**Returns:** `dict` with keys:
- `time`: Time points (hours)
- `voltage`: Voltage trajectory (V)
- `current`: Current trajectory (A)
- `soc`: SOC trajectory (dimensionless)
- `temperature`: Temperature trajectory (K)

**Implementation Details:**
```python
solution = solve_ivp(
    lambda t, y: self._battery_dynamics(t, y, current_profile(t)),
    t_span=(0, duration),
    y0=[initial_soc, initial_temperature],
    t_eval=np.arange(0, duration, dt),
    method='RK45',  # 4th-order Runge-Kutta with adaptive stepping
    rtol=1e-4,      # Relative tolerance
    atol=1e-6       # Absolute tolerance
)
```

**Why RK45?**
The Runge-Kutta-Fehlberg method provides adaptive step-size control, essential for stiff ODEs during rapid current transients. The tolerances balance accuracy against computation time.

---

#### `apply_constant_current(self, current, duration, dt=1.0)`

**Purpose:** Convenience wrapper for constant-current discharge/charge tests.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `current` | float | Constant current (A). Positive = discharge, Negative = charge |
| `duration` | float | Test duration in seconds |
| `dt` | float | Output time step in seconds |

**Returns:** Same as `simulate()`

**Use Case:** Standard battery characterization tests (C-rate discharge, capacity measurement).

---

#### `apply_drive_cycle(self, power_profile, duration, dt=1.0)`

**Purpose:** Simulates battery response to power-based (rather than current-based) profiles.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `power_profile` | callable | Function `f(t) -> power` returning power demand in Watts |
| `duration` | float | Duration in seconds |
| `dt` | float | Time step in seconds |

**Returns:** Same as `simulate()`

**Algorithm:**
Internally converts power to current at each timestep using instantaneous voltage:
```python
def current_profile(t):
    power = power_profile(t)
    voltage = self._calculate_voltage(self.current_soc)
    if abs(power) < 1e-6:
        return 0.0
    return power / voltage  # I = P / V
```

**Limitation:** Uses current SOC for voltage estimation, introducing slight error in rapidly-varying profiles. For high accuracy, an iterative solver would be needed.

---

#### `get_state(self)`

**Purpose:** Returns current battery state as a dictionary for external monitoring.

**Returns:** `dict` with keys:
- `soc`: Current state of charge
- `voltage`: Current terminal voltage (V)
- `temperature`: Current temperature (K)
- `capacity`: Battery capacity (Ah)

---

#### `plot_results(self)`

**Purpose:** Generates a 2x2 subplot visualization of simulation results.

**Returns:** `tuple(fig, axes)` - Matplotlib figure and axes array

**Plots:**
1. **Voltage vs Time**: Shows charge/discharge voltage profile
2. **Current vs Time**: Applied current waveform
3. **SOC vs Time**: Charge depletion/recovery curve
4. **Temperature vs Time**: Thermal response (converted to °C)

---

### 1.2 EnhancedBatteryModel

**Location:** `ev_digital_twin/battery_model/enhanced_battery_model.py`

An advanced battery model extending the simplified version with:
- Cell-level granularity (series/parallel configuration)
- State of Health (SOH) tracking
- Remaining Useful Life (RUL) estimation
- Degradation modeling

---

#### `__init__(self, initial_soc=1.0, capacity=3.4, nominal_voltage=3.7, num_cells_series=96, num_cells_parallel=4, initial_soh=1.0)`

**Purpose:** Initializes battery pack with cell-level configuration and degradation parameters.

**Additional Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_cells_series` | int | 96 | Cells in series (determines pack voltage) |
| `num_cells_parallel` | int | 4 | Parallel strings (determines pack capacity) |
| `initial_soh` | float | 1.0 | Starting state of health (0.0 to 1.0) |

**Derived Properties:**
- `total_cells = num_cells_series * num_cells_parallel`
- `cell_capacity = capacity / num_cells_parallel`
- `cell_nominal_voltage = nominal_voltage / num_cells_series`
- `cell_r_internal = r_internal * num_cells_parallel / num_cells_series`

**Degradation Parameters:**
- `cycle_degradation_rate = 0.0002`: SOH loss per full equivalent cycle
- `calendar_degradation_rate = 0.00005`: SOH loss per day (calendar aging)
- `temperature_factor = 0.005`: Accelerated degradation above 25°C
- `dod_factor = 1.5`: Depth-of-discharge impact multiplier

---

#### `_calculate_cell_voltage(self, soc)`

**Purpose:** Computes individual cell voltage (same algorithm as simplified model).

**Returns:** `float` - Single cell voltage (pack voltage = cell_voltage × cells_series)

---

#### `_calculate_voltage(self, soc)`

**Purpose:** Computes full pack voltage by scaling cell voltage.

**Formula:** `V_pack = V_cell × num_cells_series`

---

#### `_update_cell_states(self, soc, temperature, current)`

**Purpose:** Propagates pack-level states to individual cell arrays with simulated imbalance.

**Algorithm:**
```python
cell_current = current / num_cells_parallel  # Current division in parallel strings

for each cell i:
    # Introduce realistic cell-to-cell variations
    soc_variation = np.random.normal(0, 0.01)  # 1% σ
    temp_variation = np.random.normal(0, 1.0)  # 1K σ
    
    cell_soc[i] = clip(soc + soc_variation, 0, 1)
    cell_temperature[i] = max(ambient_temp, temperature + temp_variation)
    cell_current[i] = cell_current
    cell_voltage[i] = calculate_cell_voltage(cell_soc[i])
```

**Purpose:** Simulates real-world cell imbalances due to manufacturing tolerances, which affect pack performance and lifespan.

---

#### `_update_degradation(self, soc, temperature, current, time_step)`

**Purpose:** Updates battery health based on usage patterns using empirical degradation models.

**Degradation Mechanisms:**

**1. Cycle Aging (Usage-based):**
```python
# Track depth of discharge for each cycle
if cycle_completed:
    dod = max_soc_in_cycle - min_soc_in_cycle
    cycle_count += dod  # Partial cycle counting
    
    # DOD stress factor: deeper cycles degrade more
    cycle_degradation = cycle_degradation_rate * dod * dod_factor
    current_soh -= cycle_degradation
```

**2. Calendar Aging (Time-based):**
```python
days_step = time_step / 86400  # Convert to days
calendar_degradation = calendar_degradation_rate * days_step
```

**3. Temperature-Accelerated Aging:**
```python
temp_celsius = temperature - 273.15
if temp_celsius > 25:
    temp_degradation = temperature_factor * (temp_celsius - 25) * days_step
```

**Arrhenius Principle:** Temperature acceleration follows the rule of thumb that reaction rates double for every ~10°C increase.

---

#### `_estimate_rul_cycles(self)`

**Purpose:** Predicts remaining cycles until end-of-life (SOH = 80%).

**Algorithm:**
```python
if current_soh <= 0.8:
    return 0  # EOL reached

avg_dod = mean(cycle_depths) or 0.8  # Default assumption
degradation_per_cycle = cycle_degradation_rate * avg_dod * dod_factor
remaining_soh = current_soh - 0.8  # Distance to EOL threshold
remaining_cycles = remaining_soh / degradation_per_cycle
```

**Note:** Returns cycles to 80% capacity, the industry-standard automotive EOL criterion.

---

#### `_estimate_rul_calendar(self)`

**Purpose:** Predicts remaining calendar days until EOL based on time-based degradation.

**Algorithm:**
```python
avg_temp = mean(temperature_data) or ambient_temp
temp_factor_effect = temperature_factor * max(0, avg_temp_celsius - 25)
degradation_per_day = calendar_degradation_rate + temp_factor_effect
remaining_days = (current_soh - 0.8) / degradation_per_day
```

---

#### `get_state(self)`

**Purpose:** Returns comprehensive battery state including cell-level statistics.

**Returns:** Extended dictionary with:
- Basic states: `soc`, `voltage`, `temperature`
- Health metrics: `soh`, `rul_cycles`, `rul_calendar_days`
- Usage statistics: `cycle_count`, `energy_throughput`
- Cell statistics: `cell_config`, `total_cells`, min/max values for SOC, voltage, temperature, SOH

---

#### `plot_cell_distribution(self)`

**Purpose:** Visualizes cell-to-cell parameter variations as heatmaps.

**Visualization:**
Reshapes 1D cell arrays into 2D grids (`num_series × num_parallel`) and displays:
1. SOC distribution (viridis colormap)
2. Voltage distribution (plasma colormap)
3. Temperature distribution (inferno colormap)
4. SOH distribution (cividis colormap)

**Use Case:** Identifying weak/degraded cells for maintenance decisions.

---

### 1.3 BatteryDFNModel

**Location:** `ev_digital_twin/battery_model/battery_dfn_model.py`

A PyBaMM-based implementation using the Doyle-Fuller-Newman electrochemical model (physics-based rather than equivalent circuit).

**Note:** This model was intended for high-fidelity simulation but encountered solver convergence issues. The simplified models are used instead for production simulations.

---

#### `__init__(self, initial_soc=1.0, capacity=3.4, nominal_voltage=3.7)`

**Purpose:** Initializes PyBaMM DFN model wrapper.

**Key Difference:** Uses PyBaMM's built-in solver and parameter sets rather than custom ODE implementation.

---

#### `create_simulation(self, experiment=None)`

**Purpose:** Constructs a PyBaMM simulation object with the DFN electrochemical model.

**Algorithm:**
```python
model = pybamm.lithium_ion.DFN()  # Doyle-Fuller-Newman model
parameter_values = pybamm.ParameterValues("Marquis2019")  # Literature parameters

# Override with user-specified values
parameter_values.update({
    "Nominal cell capacity [A.h]": self.capacity,
    "Initial concentration in negative electrode": f(initial_soc),
    "Initial concentration in positive electrode": f(1 - initial_soc),
    "Initial temperature [K]": 298.15
})

# Solver configuration for numerical stability
solver = pybamm.CasadiSolver(mode="safe", dt_max=60.0)
```

**Fallback:** If DFN fails to converge, automatically falls back to the simpler SPM (Single Particle Model).

---

#### `run_simulation(self, t_eval=None)`

**Purpose:** Executes the PyBaMM simulation with error handling.

**Error Handling:**
```python
try:
    self.solution = self.simulation.solve(t_eval)
except pybamm.SolverError:
    # Fall back to SPM model with relaxed solver settings
    model = pybamm.lithium_ion.SPM()
    solver = pybamm.CasadiSolver(mode="safe", dt_max=30.0)
```

---

#### `apply_current(self, current, duration, dt=1.0)`

**Purpose:** Creates and runs a constant-current experiment.

**Experiment Definition:**
```python
if current > 0:
    experiment = pybamm.Experiment([
        f"Discharge at {abs(current)/capacity}C for {duration} seconds"
    ])
else:
    experiment = pybamm.Experiment([
        f"Charge at {abs(current)/capacity}C for {duration} seconds"
    ])
```

---

## 2. Motor Models

### 2.1 SimplifiedPMSMMotorModel

**Location:** `ev_digital_twin/motor_model/simplified_pmsm_motor_model.py`

A simplified Permanent Magnet Synchronous Motor (PMSM) model using field-oriented control (FOC) principles and ODE-based dynamics.

---

#### `__init__(self, nominal_power=100.0, nominal_speed=4000.0, nominal_voltage=400.0)`

**Purpose:** Initializes PMSM model with electrical and mechanical parameters.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `nominal_power` | float | 100.0 | Rated power (kW) |
| `nominal_speed` | float | 4000.0 | Rated speed (rpm) |
| `nominal_voltage` | float | 400.0 | DC link voltage (V) |

**Derived Parameters:**
```python
nominal_torque = (nominal_power * 1000) / (nominal_speed * 2π / 60)  # T = P / ω
```

**Motor Electrical Parameters:**
- `r_stator = 0.05`: Stator winding resistance (Ω)
- `l_d = 0.001`: d-axis inductance (H) - direct magnetic axis
- `l_q = 0.001`: q-axis inductance (H) - quadrature magnetic axis
- `psi_pm = 0.1`: Permanent magnet flux linkage (Wb)
- `pole_pairs = 3`: Number of magnetic pole pairs
- `j_rotor = 0.01`: Rotor moment of inertia (kg·m²)
- `b_friction = 0.001`: Viscous friction coefficient (Nm·s/rad)
- `max_current = 300.0`: Peak current limit (A)

---

#### `_motor_dynamics(self, t, state, torque_load)`

**Purpose:** Defines the electromechanical ODE system in the d-q reference frame.

**State Vector:** `[ω, i_d, i_q]`
- ω: Angular velocity (rad/s)
- i_d: d-axis current (A) - field current
- i_q: q-axis current (A) - torque-producing current

**Electromagnetic Torque Equation:**
```python
T_em = 1.5 * p * [(L_d - L_q) * i_d * i_q + ψ_pm * i_q]
```
Where:
- First term: Reluctance torque (zero if L_d = L_q)
- Second term: Permanent magnet torque

**Speed Dynamics (Newton's Second Law):**
```python
dω/dt = (T_em - T_load - B * ω) / J
```

**Current Dynamics (Field-Oriented Control):**
```python
# Field weakening above nominal speed
if |ω| > ω_nominal:
    i_d_ref = -0.2 * I_max * (|ω| - ω_nominal) / ω_nominal  # Negative d-current
else:
    i_d_ref = 0  # MTPA (Maximum Torque Per Ampere)

# Torque control via q-axis current
i_q_ref = (2 * T_load) / (3 * p * ψ_pm)

# First-order lag dynamics for current control
τ_i = 0.001  # Current loop time constant
di_d/dt = (i_d_ref - i_d) / τ_i
di_q/dt = (i_q_ref - i_q) / τ_i
```

**Field Weakening Explanation:** Above base speed, d-axis current is injected to reduce back-EMF, enabling higher speeds at reduced torque (constant power region).

---

#### `_calculate_voltages(self, omega, i_d, i_q)`

**Purpose:** Computes d-q axis voltages from the PMSM voltage equations.

**Voltage Equations:**
```python
v_d = R * i_d - ω_elec * L_q * i_q          # d-axis: resistive drop - q-axis coupling
v_q = R * i_q + ω_elec * L_d * i_d + ω_elec * ψ_pm  # q-axis: resistive + d-coupling + back-EMF
```

Where `ω_elec = ω_mech * pole_pairs` (electrical frequency).

---

#### `_dq_to_abc(self, theta, i_d, i_q)`

**Purpose:** Transforms d-q currents to three-phase (abc) frame using inverse Park transformation.

**Transformation:**
```python
i_a = i_d * cos(θ) - i_q * sin(θ)
i_b = i_d * cos(θ - 120°) - i_q * sin(θ - 120°)
i_c = i_d * cos(θ - 240°) - i_q * sin(θ - 240°)
```

Where θ is the electrical rotor angle.

---

#### `_calculate_efficiency(self, omega, torque, i_d, i_q)`

**Purpose:** Computes motor efficiency accounting for multiple loss mechanisms.

**Loss Breakdown:**
```python
# Mechanical power output
P_mech = |ω * T|

# Copper losses (I²R in stator windings)
P_copper = R_s * (i_d² + i_q²)

# Iron losses (core losses, proportional to ω²)
P_iron = 0.01 * ω²  # Simplified eddy current + hysteresis

# Friction losses (bearing and windage)
P_friction = B * ω²

# Total electrical input
P_elec = P_mech + P_copper + P_iron + P_friction

# Efficiency (motoring mode)
η = P_mech / P_elec
```

**Regeneration Mode:** Returns fixed 90% efficiency when torque is negative (generator operation).

---

#### `simulate(self, torque_profile, duration, dt=0.001)`

**Purpose:** Simulates motor response to torque command profile.

**Note:** Default `dt=0.001s` (1ms) is necessary due to fast electrical dynamics (current control loops).

---

#### `run_speed_profile(self, speed_profile, duration, dt=0.001)`

**Purpose:** Runs motor with speed reference using embedded PI controller.

**PI Controller:**
```python
kp = 0.5  # Proportional gain
ki = 0.1  # Integral gain

def torque_controller(t):
    target_rpm = speed_profile(t)
    target_rads = target_rpm * 2π / 60
    current_rads = self.current_speed * 2π / 60
    
    error = target_rads - current_rads
    integral += error * dt
    
    torque = kp * error + ki * integral
    return clip(torque, -2 * T_nominal, 2 * T_nominal)
```

---

### 2.2 EnhancedPMSMMotorModel

**Location:** `ev_digital_twin/motor_model/enhanced_motor_model.py`

Extended PMSM model with thermal dynamics, degradation tracking, and RUL estimation.

---

#### `__init__(self, nominal_power=150.0, nominal_speed=8000.0, nominal_voltage=400.0, motor_type="PMSM", pole_pairs=4, initial_health=1.0)`

**Purpose:** Initializes motor with thermal and health monitoring capabilities.

**Additional Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `motor_type` | str | "PMSM" | Motor type identifier |
| `pole_pairs` | int | 4 | Number of pole pairs |
| `initial_health` | float | 1.0 | Starting health factor |

**Thermal Parameters:**
- `thermal_resistance = 0.05`: Thermal resistance to ambient (K/W)
- `thermal_capacitance = 5000.0`: Thermal mass (J/K)
- `ambient_temp = 298.15`: Ambient temperature (K)
- `max_temp = 423.15`: Maximum allowed temperature (K) - 150°C

**Efficiency Map Parameters:**
- `base_efficiency = 0.92`: Peak efficiency at nominal operation
- `copper_loss_factor = 0.6`: I²R losses proportion
- `iron_loss_factor = 0.3`: Core losses proportion
- `mechanical_loss_factor = 0.1`: Friction losses proportion

**Wear Parameters:**
- `thermal_wear_factor = 0.0001`: Health degradation per hour at max temperature
- `current_wear_factor = 0.0002`: Health degradation per hour at max current
- `mechanical_wear_factor = 0.0001`: Health degradation per hour at max speed

---

#### `_motor_dynamics(self, t, state, torque_load)`

**Purpose:** Enhanced ODE system including thermal dynamics.

**State Vector:** `[ω, T]` (angular velocity, temperature)

**Temperature Dynamics:**
```python
# Loss calculation
P_copper = 1.5 * R_s * (i_d² + i_q²)
P_iron = 0.01 * (ω / ω_nominal)² * P_nominal
P_mech = 0.005 * (ω / ω_nominal)³ * P_nominal

P_loss = P_copper + P_iron + P_mech

# Thermal balance
P_cooling = (T - T_ambient) / R_thermal
dT/dt = (P_loss - P_cooling) / C_thermal
```

---

#### `_update_degradation(self, speed, torque, temperature, time_step)`

**Purpose:** Tracks motor wear based on stress factors.

**Wear Model:**
```python
hours = time_step / 3600

# Normalized stress factors
norm_speed = speed / nominal_speed
norm_torque = torque / nominal_torque
norm_temp = (temperature - T_ambient) / (T_max - T_ambient)

# Track high-stress operation hours
if temperature > 373.15:  # > 100°C
    high_temp_hours += hours
if abs(torque) > nominal_torque:
    high_current_hours += hours
if abs(speed) > nominal_speed:
    high_speed_hours += hours

# Calculate wear (squared stress factors = accelerated wear)
thermal_wear = thermal_wear_factor * hours * max(0, norm_temp)²
current_wear = current_wear_factor * hours * max(0, norm_torque)²
mechanical_wear = mechanical_wear_factor * hours * max(0, norm_speed)²

current_health -= (thermal_wear + current_wear + mechanical_wear)
```

---

#### `_estimate_rul(self)`

**Purpose:** Predicts remaining motor life in operating hours.

**Algorithm:**
```python
if current_health <= 0.7:
    return 0  # EOL threshold at 70% health

if operation_hours > 0:
    avg_degradation_rate = (initial_health - current_health) / operation_hours
else:
    # Default estimate based on nominal conditions
    avg_degradation_rate = 0.5 * sum(wear_factors)

remaining_health = current_health - 0.7
remaining_hours = remaining_health / avg_degradation_rate
```

---

#### `_calculate_efficiency(self, speed, torque)`

**Purpose:** Computes efficiency with operating point and health derating.

**Algorithm:**
```python
efficiency = base_efficiency  # 92%

# Derating at low operating points
if norm_speed < 0.2 or |norm_torque| < 0.2:
    efficiency *= 0.7 + 0.3 * min(norm_speed, |norm_torque|) / 0.2

# Derating at high speed (field weakening region)
if norm_speed > 1.0:
    efficiency *= 1.0 - 0.1 * (norm_speed - 1.0) / 0.2

# Derating at high torque (thermal stress)
if |norm_torque| > 1.0:
    efficiency *= 1.0 - 0.05 * (|norm_torque| - 1.0) / 0.2

# Health derating
efficiency *= 0.7 + 0.3 * current_health

return clip(efficiency, 0.1, 0.98)
```

---

#### `apply_speed_profile(self, speed_profile, duration, dt=1.0, controller_kp=10.0, controller_ki=1.0)`

**Purpose:** Runs motor with configurable PI controller gains.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `controller_kp` | float | 10.0 | Proportional gain |
| `controller_ki` | float | 1.0 | Integral gain |

---

#### `plot_efficiency_map(self, speed_range=None, torque_range=None)`

**Purpose:** Generates motor efficiency contour map.

**Visualization:**
- X-axis: Speed (rpm)
- Y-axis: Torque (Nm)
- Color: Efficiency (%)
- Overlays: Nominal point, peak torque, max speed, constant power curves

---

### 2.3 PMSMMotorModel

**Location:** `ev_digital_twin/motor_model/pmsm_motor_model.py`

GYM Electric Motor library-based implementation (reinforcement learning environment).

**Note:** Encountered parameter compatibility issues; simplified model is used instead.

---

#### `_create_pmsm_environment(self)`

**Purpose:** Creates GYM electric motor environment for RL-style simulation.

**Environment Configuration:**
```python
env = gem.make(
    "Cont-SC-PMSM-v0",  # Continuous Speed Control PMSM
    visualization=MotorDashboard(...),
    motor_parameter={
        p=3, l_d=0.0014, l_q=0.0014,
        psi_p=0.1, r_s=0.05, j_rotor=0.001
    },
    nominal_values={...},
    limit_values={...},
    load_parameter={j_load=0.1, a=0.01}
)
```

---

#### `step(self, action)`

**Purpose:** Advances simulation by one timestep with control action.

**Interface:** Compatible with OpenAI Gym API:
```python
state, reward, terminated, truncated, info = env.step(action)
```

---

## 3. Integration Layer

### 3.1 ElectricVehicleDigitalTwin

**Location:** `ev_digital_twin/integration/ev_digital_twin.py`

Integrates battery and motor models with vehicle dynamics for complete EV simulation.

---

#### `__init__(self, battery_capacity=50.0, ...)`

**Purpose:** Constructs EV model with powertrain and vehicle specifications.

**Vehicle Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vehicle_mass` | float | 1500.0 | Total mass (kg) |
| `wheel_radius` | float | 0.3 | Tire radius (m) |
| `gear_ratio` | float | 10.0 | Final drive ratio |
| `drag_coefficient` | float | 0.3 | Aerodynamic Cd |
| `frontal_area` | float | 2.0 | Frontal area (m²) |
| `rolling_resistance` | float | 0.01 | Rolling resistance Crr |

**Physical Constants:**
- `air_density = 1.225`: Air density (kg/m³)
- `gravity = 9.81`: Gravitational acceleration (m/s²)

---

#### `_calculate_resistive_forces(self, speed)`

**Purpose:** Computes total road load forces.

**Force Components:**
```python
# Rolling resistance (approximately constant)
F_rolling = Crr * m * g

# Aerodynamic drag (speed-squared dependent)
F_drag = 0.5 * ρ * Cd * A * v²

# Total resistance
F_total = F_rolling + F_drag
```

**Physical Interpretation:**
- Rolling resistance dominates at low speeds (~100N for 1500kg vehicle)
- Aero drag dominates above ~50 km/h (quadratic growth)

---

#### `_speed_to_motor_rpm(self, speed)`

**Purpose:** Converts vehicle speed to motor speed through drivetrain.

**Formula:**
```python
wheel_rpm = speed / (2π * wheel_radius) * 60
motor_rpm = wheel_rpm * gear_ratio
```

---

#### `_motor_rpm_to_speed(self, motor_rpm)`

**Purpose:** Inverse conversion from motor speed to vehicle speed.

---

#### `_torque_to_force(self, torque)`

**Purpose:** Converts motor torque to wheel tractive force.

**Formula:**
```python
F = T * gear_ratio / wheel_radius
```

**Derivation:** Power conservation through gearbox: `P = T_motor * ω_motor = F * v`

---

#### `_force_to_torque(self, force)`

**Purpose:** Inverse conversion from wheel force to motor torque.

---

#### `_calculate_power_demand(self, speed, acceleration)`

**Purpose:** Computes instantaneous power requirement.

**Formula:**
```python
F_resistive = rolling_resistance + aero_drag
F_acceleration = m * a
F_total = F_resistive + F_acceleration

P = F_total * v  # Watts
P_kW = P / 1000
```

**Sign Convention:**
- Positive power: Propulsion (battery discharging, motor driving)
- Negative power: Regeneration (battery charging, motor generating)

---

#### `simulate(self, speed_profile, duration, dt=1.0)`

**Purpose:** Runs complete EV simulation with speed following.

**Simulation Loop:**
```python
for t in time_points:
    target_speed = speed_profile(t)
    acceleration = (target_speed - prev_speed) / dt
    
    # Vehicle dynamics
    motor_speed = speed_to_motor_rpm(target_speed)
    resistive_force = calculate_resistive_forces(target_speed)
    acceleration_force = mass * acceleration
    motor_torque = force_to_torque(resistive_force + acceleration_force)
    power_demand = calculate_power_demand(target_speed, acceleration)
    
    # Battery response
    battery_current = (power_demand * 1000) / battery_voltage
    battery.apply_constant_current(battery_current, dt)
    
    # Motor response
    motor.simulate(lambda t: motor_torque, dt)
    
    # Store results...
```

---

#### `export_to_csv(self, filename)`

**Purpose:** Exports simulation results to CSV format.

**Columns Include:**
- Time (s), Speed (m/s), Acceleration (m/s²), Distance (m)
- Power Demand (kW)
- Battery: SOC, Voltage (V), Current (A), Temperature (°C)
- Motor: Speed (rpm), Torque (Nm), Efficiency (%)

---

### 3.2 EnhancedElectricVehicleDigitalTwin

**Location:** `ev_digital_twin/integration/enhanced_ev_digital_twin.py`

Extended EV model with:
- Enhanced battery/motor models
- Energy accounting
- Time tracking (seconds, minutes, formatted)
- Health monitoring
- Report generation

---

#### `_format_time(self, seconds)`

**Purpose:** Converts seconds to mm:ss display format.

**Format:** `f"{minutes:02d}:{seconds:02d}"`

---

#### `_calculate_motor_torque(self, power_demand, motor_speed)`

**Purpose:** Computes motor torque from power and speed.

**Formula:**
```python
P_watts = power_demand * 1000
ω_rad_s = motor_speed * 2π / 60

if abs(ω_rad_s) < 1e-6:
    return 0.0  # Avoid division by zero at standstill

T = P_watts / ω_rad_s
```

---

#### `_update_energy_consumption(self, power_demand, dt)`

**Purpose:** Accumulates energy usage with efficiency tracking.

**Algorithm:**
```python
energy_step = power_demand * dt / 3600  # kWh

if power_demand > 0:  # Only count propulsion energy
    current_energy_consumption += energy_step

distance_km = current_distance / 1000
if distance_km > 0.001:
    current_energy_efficiency = current_energy_consumption / distance_km  # kWh/km
```

---

#### `simulate(self, speed_profile, duration, dt=0.1)`

**Purpose:** Enhanced simulation with proportional speed controller.

**Speed Controller:**
```python
kp = 0.5  # Proportional gain
speed_error = target_speed - current_speed
acceleration = clip(kp * speed_error, -5.0, 5.0)  # Limit to ±5 m/s²
current_speed = max(0, current_speed + acceleration * dt)
```

---

#### `generate_report(self, filename="ev_simulation_report.md")`

**Purpose:** Creates comprehensive Markdown report.

**Report Sections:**
1. Simulation Overview (duration, distance, energy)
2. Vehicle Performance (speed, acceleration statistics)
3. Battery Status (SOC, SOH, RUL, temperature)
4. Motor Status (performance, health, RUL)
5. Vehicle Specifications
6. Component Specifications
7. Timestamp

---

## 4. Simulation Interfaces

### 4.1 RealTimeEVSimulation

**Location:** `ev_digital_twin/simulation/real_time_simulation.py`

Interactive simulation interface with real-time visualization and control.

---

#### `__init__(self, ev_model=None)`

**Purpose:** Initializes real-time interface with default or custom EV model.

**Default Configuration:**
- `dt = 0.1`: 100ms timestep
- `max_time = 300`: 5-minute maximum
- `max_speed = 40`: 144 km/h limit
- `acceleration_rate = 3.0`: 3 m/s² default acceleration
- `deceleration_rate = 5.0`: 5 m/s² default braking

---

#### `_simulation_loop(self)`

**Purpose:** Background thread running continuous simulation.

**Thread Loop:**
```python
while running and current_time < max_time:
    if not paused:
        results = ev.simulate(speed_profile, dt, dt)
        current_time += dt
        
        # Store data for visualization
        time_data.append(current_time)
        speed_data.append(results["speed"][-1])
        battery_soc_data.append(results["battery_soc"][-1])
        ...
    
    time.sleep(dt * 0.5)  # Yield CPU time
```

---

#### `start_simulation(self)`

**Purpose:** Launches simulation in daemon thread.

```python
running = True
paused = False
simulation_thread = threading.Thread(target=_simulation_loop)
simulation_thread.daemon = True  # Dies with main thread
simulation_thread.start()
```

---

#### `pause_simulation(self)` / `resume_simulation(self)`

**Purpose:** Thread-safe pause/resume via `paused` flag.

---

#### `stop_simulation(self)`

**Purpose:** Terminates simulation thread with timeout.

```python
running = False
if simulation_thread:
    simulation_thread.join(timeout=1.0)
```

---

#### `set_target_speed(self, speed)`

**Purpose:** Sets target speed with bounds checking.

```python
target_speed = min(max(0, speed), max_speed)
```

---

#### `accelerate(self, amount=None)` / `decelerate(self, amount=None)`

**Purpose:** Incremental speed adjustments.

Default amounts: `acceleration_rate * dt` or `deceleration_rate * dt`

---

#### `_init_animation(self)`

**Purpose:** Sets up Matplotlib figure with interactive widgets.

**Layout:**
- 2x2 subplot grid (speed, SOC, power, distance)
- Speed slider (0 to max_speed)
- Start/Pause/Stop buttons

**Widgets:**
```python
speed_slider = Slider(ax_speed, 'Target Speed [m/s]', 0, max_speed, valinit=0)
speed_slider.on_changed(_update_speed)

start_button = Button(ax_start, 'Start')
start_button.on_clicked(_on_start)
...
```

---

#### `_update_animation(self, frame)`

**Purpose:** Animation callback updating plot data.

```python
lines["speed"].set_data(time_data, speed_data)
lines["soc"].set_data(time_data, battery_soc_data)
lines["power"].set_data(time_data, motor_power_data)
lines["distance"].set_data(time_data, [d/1000 for d in distance_data])

# Auto-scale axes if needed
if current_time > axes[0,0].get_xlim()[1]:
    for ax in axes.flat:
        ax.set_xlim(0, current_time * 1.5)
```

---

#### `run_interactive_simulation(self)`

**Purpose:** Main entry point launching animated GUI.

```python
_init_animation()
animation = FuncAnimation(fig, _update_animation, interval=100)  # 10 Hz refresh
plt.show()  # Blocking call
stop_simulation()  # Cleanup when window closed
```

---

### 4.2 EVReportingDashboard

**Location:** `ev_digital_twin/simulation/reporting_dashboard.py`

Post-simulation analysis and comparison tool.

---

#### `__init__(self, data_dir="./data_export")`

**Purpose:** Initializes dashboard with data persistence.

**Initialization:**
```python
os.makedirs(data_dir, exist_ok=True)
_load_existing_simulations()
```

---

#### `_load_existing_simulations(self)`

**Purpose:** Scans data directory for saved simulation results.

**Loading Strategy:**
1. Load metadata from `simulation_metadata.json`
2. Scan for `*_results.csv` files
3. Auto-generate metadata for orphaned CSV files

---

#### `load_simulation(self, file_path, description=None)`

**Purpose:** Imports external CSV file as new simulation.

**ID Generation:** `f"sim_{int(time.time())}"` - Unix timestamp for uniqueness

---

#### `add_simulation_result(self, data, description=None)`

**Purpose:** Adds in-memory results without pre-existing file.

**Actions:**
1. Convert dict to DataFrame if needed
2. Generate unique ID
3. Save to CSV in data directory
4. Update metadata

---

#### `list_simulations(self)`

**Purpose:** Returns DataFrame summarizing all available simulations.

**Columns:**
- Simulation ID, Timestamp, Description, File
- Summary statistics (distance, energy, final SOC, duration)

---

#### `get_simulation_summary(self, sim_id=None)`

**Purpose:** Computes comprehensive statistics for one simulation.

**Statistics Include:**
- Duration, distance
- Speed (max, avg), acceleration (max, min)
- Power (max, avg), energy (consumption, efficiency)
- Battery (initial/final SOC, temperature range, SOH, RUL)
- Motor (max speed/torque, avg efficiency, temperature, health, RUL)

---

#### `generate_dashboard(self, sim_id=None, output_file="ev_dashboard.png")`

**Purpose:** Creates multi-panel visualization figure.

**Dashboard Layout (12x6 GridSpec):**
1. Title/summary text (rows 0-1)
2. Speed/distance plot (rows 2-3)
3. Power/energy plot (rows 4-5)
4. Battery metrics (rows 6-7)
5. Motor metrics (rows 8-9)
6. Health/RUL trends (rows 10-11)

---

## 5. Launcher Utilities

### `setup_paths()`

**Location:** `enhanced_ev_launcher.py`, `web_interface_launcher.py`, `enhanced_real_time_simulation.py`

**Purpose:** Configures Python path for Windows compatibility.

**Algorithm:**
```python
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

ev_twin_dir = os.path.join(current_dir, "ev_digital_twin")
if os.path.exists(ev_twin_dir) and ev_twin_dir not in sys.path:
    sys.path.insert(0, ev_twin_dir)
```

---

### `check_dependencies()`

**Location:** `enhanced_ev_launcher.py`

**Purpose:** Verifies required packages are installed.

**Required Packages:** `numpy`, `pandas`, `matplotlib`, `scipy`

```python
for package in required_packages:
    if importlib.util.find_spec(package) is None:
        missing_packages.append(package)
```

---

### `start_web_server(directory, port=8000)`

**Location:** `enhanced_ev_launcher.py`, `web_interface_launcher.py`

**Purpose:** Launches HTTP server with CORS support.

**Custom Handler Features:**
```python
class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def guess_type(self, path):
        # Correct MIME types for web resources
        if path.endswith('.js'): return 'application/javascript'
        if path.endswith('.html'): return 'text/html'
        ...
```

**Threading:**
```python
server_thread = threading.Thread(target=httpd.serve_forever)
server_thread.daemon = True
server_thread.start()
```

---

### `find_index_html()`

**Location:** `enhanced_ev_launcher.py`, `web_interface_launcher.py`

**Purpose:** Locates web interface files in project structure.

**Search Order:**
1. Current directory
2. `./web_interface/`
3. `./ev_digital_twin/web_interface/`
4. Recursive search from current directory
5. Fallback to current directory

---

### `open_web_interface(port=8000)`

**Purpose:** Opens browser to simulation interface.

```python
webbrowser.open(f"http://localhost:{port}/index.html")
```

---

### `start_simulation_backend()`

**Location:** `enhanced_ev_launcher.py`

**Purpose:** Launches simulation process in background.

**Windows-Specific:**
```python
if platform.system() == "Windows":
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # Hide console
    
    process = subprocess.Popen(
        [sys.executable, sim_script],
        cwd=current_dir,
        startupinfo=startupinfo
    )
```

---

## Appendix: Key Physical Equations Summary

### Battery
| Equation | Description |
|----------|-------------|
| `dSOC/dt = -I / (C × 3600)` | Coulomb counting |
| `dT/dt = (I²R - k(T-T_amb)) / C_th` | Thermal balance |
| `V = f(SOC)` | Nonlinear voltage curve |

### Motor
| Equation | Description |
|----------|-------------|
| `T_em = 1.5p(ψ_pm·i_q + (L_d-L_q)·i_d·i_q)` | Electromagnetic torque |
| `dω/dt = (T_em - T_load - Bω) / J` | Mechanical dynamics |
| `v_q = Ri_q + ωL_di_d + ωψ_pm` | q-axis voltage |

### Vehicle
| Equation | Description |
|----------|-------------|
| `F_rolling = C_rr × m × g` | Rolling resistance |
| `F_drag = ½ρC_dAv²` | Aerodynamic drag |
| `P = (F_roll + F_drag + ma) × v` | Power demand |
| `T_motor = F_wheel × r_wheel / G_r` | Motor torque requirement |

---

*Documentation generated for AutoPulse EV Digital Twin - Version 1.0*
