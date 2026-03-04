# ⚡ AutoPulse — Electric Vehicle Digital Twin (Windows Edition)

> A high-fidelity, real-time **Electric Vehicle Digital Twin** that integrates physics-based battery and motor models with an interactive web dashboard — engineered for simulation, analysis, and predictive maintenance research.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?logo=windows)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Component Breakdown](#component-breakdown)
5. [Data Flow & Simulation Workflow](#data-flow--simulation-workflow)
6. [Project Structure](#project-structure)
7. [Installation](#installation)
8. [Usage](#usage)
9. [Configuration Parameters](#configuration-parameters)
10. [Tech Stack](#tech-stack)

---

## Overview

**AutoPulse** is a modular, physics-based digital twin platform for electric vehicles. It replicates the real-time behaviour of an EV's powertrain — from lithium-ion battery electrochemistry to PMSM motor electrodynamics — and exposes the live simulation state through an interactive browser-based dashboard.

The platform is designed for:
- **EV Powertrain Research** — Validate battery and motor control strategies before hardware deployment.
- **Predictive Maintenance** — Track Remaining Useful Life (RUL) of battery packs and motor windings.
- **Drive Cycle Analysis** — Replay standard or custom drive cycles and observe energy consumption patterns.
- **Education & Prototyping** — A self-contained environment to learn EV physics without hardware.

---

## Key Features

| Feature | Description |
|---|---|
| 🔋 Battery Digital Twin | SOC, voltage, current, temperature tracking with thermal dynamics |
| ⚙️ PMSM Motor Model | d-q axis 3-phase motor model with torque, speed, and efficiency curves |
| 🚗 Vehicle Dynamics | Aerodynamic drag, rolling resistance, gear ratio, and road force integration |
| 📊 Real-Time Dashboard | Live charts via web browser — no extra software needed |
| 🔮 RUL Prediction | Data-driven Remaining Useful Life estimation for battery and motor |
| 📁 Data Export | Simulation runs automatically exported to CSV for offline analysis |
| 🪟 Windows-Native | One-click `.bat` launchers — no CLI knowledge required |

---

## System Architecture

The platform is decomposed into three independent physics layers that feed into a central integration layer, which in turn drives the real-time simulation and web interface.

```mermaid
graph TB
    subgraph INPUT["🎮 Inputs"]
        DC[Drive Cycle / Speed Profile]
        PARAMS[Vehicle Parameters]
        CFG[User Configuration]
    end

    subgraph PHYSICS["⚙️ Physics Models"]
        BAT["🔋 Battery Model<br/>(SOC · Voltage · Temperature · RUL)"]
        MOT["🔌 PMSM Motor Model<br/>(Torque · Speed · Efficiency · d-q Axis)"]
        VEH["🚗 Vehicle Dynamics<br/>(Drag · Rolling Resistance · Gear Ratio)"]
    end

    subgraph INTEGRATION["🔗 Integration Layer"]
        TWIN["EV Digital Twin<br/>ev_digital_twin.py"]
    end

    subgraph SIM["📡 Simulation Engine"]
        RTS["Real-Time Simulation<br/>real_time_simulation.py"]
        ENH["Enhanced Simulation<br/>enhanced_real_time_simulation.py"]
    end

    subgraph OUTPUT["📤 Outputs"]
        WEB["🌐 Web Dashboard<br/>(Live Charts)"]
        CSV["📄 CSV Export<br/>(Data Archive)"]
        DASH["📊 Reporting Dashboard<br/>(Post-Analysis)"]
    end

    DC --> TWIN
    PARAMS --> TWIN
    CFG --> TWIN

    TWIN --> BAT
    TWIN --> MOT
    TWIN --> VEH

    BAT --> INTEGRATION
    MOT --> INTEGRATION
    VEH --> INTEGRATION

    TWIN --> RTS
    TWIN --> ENH

    RTS --> WEB
    RTS --> CSV
    ENH --> DASH
    ENH --> CSV
```

---

## Component Breakdown

### 🔋 Battery Model

Implements a simplified electrochemical model of a lithium-ion cell / pack.

```mermaid
graph LR
    SOC["State of Charge<br/>(SOC)"] --> OCV["Open Circuit Voltage<br/>OCV = f(SOC)"]
    OCV --> VTERM["Terminal Voltage<br/>V_t = OCV − I·R_int"]
    VTERM --> HEAT["Heat Generation<br/>Q = I²·R_int"]
    HEAT --> TEMP["Temperature<br/>Thermal ODE"]
    TEMP --> COOL["Cooling Loss<br/>Q_cool = h·(T−T_amb)"]
    COOL --> TEMP
    SOC --> RUL["RUL Estimation<br/>(Capacity Fade)"]
```

**Key parameters modelled:**
- State of Charge (SOC) via Coulomb counting
- Terminal voltage with internal resistance drop
- Thermal dynamics (heat generation + convective cooling)
- Capacity fade for degradation / RUL tracking

---

### ⚙️ PMSM Motor Model

Implements a Permanent Magnet Synchronous Motor in the rotating d-q reference frame.

```mermaid
graph LR
    SPD["Speed Command<br/>(rpm)"] --> CTRL["Field-Oriented Control<br/>(FOC)"]
    CTRL --> DQ["d-q Current Control<br/>i_d, i_q"]
    DQ --> TRQ["Electromagnetic Torque<br/>T_e = 1.5·p·ψ_pm·i_q"]
    TRQ --> DYN["Mechanical Dynamics<br/>J·dω/dt = T_e − T_l − B·ω"]
    DYN --> SPD2["Actual Speed<br/>(rad/s → rpm)"]
    DQ --> EFF["Efficiency Map<br/>η = P_mech / P_elec"]
    SPD2 --> BAT2["Power Draw<br/>→ Battery Model"]
```

**Key parameters modelled:**
- d-q axis stator inductances and resistance
- Permanent magnet flux linkage (ψ_pm)
- Rotor inertia and friction torque
- 3-phase current/voltage reconstruction
- Motor efficiency at each operating point

---

### 🚗 Vehicle Dynamics

Links motor torque output to real-world vehicle motion.

```mermaid
graph LR
    TRQ["Motor Torque<br/>(Nm)"] --> GEAR["Gear Ratio Scaling<br/>T_wheel = T_mot × G"]
    GEAR --> FORCE["Tractive Force<br/>F_t = T_wheel / R_wheel"]
    FORCE --> NET["Net Force<br/>F_net = F_t − F_drag − F_roll"]
    DRAG["Aero Drag<br/>F_drag = 0.5·ρ·C_d·A·v²"] --> NET
    ROLL["Rolling Resistance<br/>F_roll = μ·m·g"] --> NET
    NET --> ACC["Acceleration<br/>a = F_net / m"]
    ACC --> VEL["Velocity<br/>v(t+dt) = v(t) + a·dt"]
    VEL --> DRAG
```

---

## Data Flow & Simulation Workflow

This diagram shows the full lifecycle of one simulation time step — from user input to data export.

```mermaid
sequenceDiagram
    participant User as 🧑 User / Web UI
    participant Sim as 📡 Simulation Engine
    participant Twin as 🔗 EV Digital Twin
    participant Bat as 🔋 Battery Model
    participant Mot as ⚙️ Motor Model
    participant Veh as 🚗 Vehicle Dynamics
    participant Export as 📄 Data Export

    User->>Sim: Set target speed / drive cycle
    loop Every Δt = 0.1 s
        Sim->>Twin: step(target_speed, dt)
        Twin->>Veh: compute_road_forces(v)
        Veh-->>Twin: F_drag, F_roll
        Twin->>Mot: request_torque(T_demand)
        Mot-->>Twin: actual_torque, efficiency, P_elec
        Twin->>Bat: draw_current(I = P_elec / V)
        Bat-->>Twin: SOC, V_terminal, Temperature
        Twin-->>Sim: state {v, SOC, T_bat, T_mot, η, RUL}
        Sim-->>User: Update live dashboard charts
        Sim->>Export: Append row to CSV
    end
    User->>Sim: Stop simulation
    Sim->>Export: Flush & save final CSV
```

---

## Project Structure

```
AutoPulse_ev_digital_twin_windows/
│
├── README.md                          ← You are here
│
└── ev_digital_twin_windows/
    └── ev_digital_twin/
        │
        ├── 🔋 battery_model/
        │   ├── simplified_battery_model.py    # Core battery electrochemical model
        │   ├── enhanced_battery_model.py      # Extended model with degradation
        │   └── battery_dfn_model.py           # Doyle-Fuller-Newman (DFN) model
        │
        ├── ⚙️  motor_model/
        │   ├── simplified_pmsm_motor_model.py # d-q axis PMSM model
        │   ├── enhanced_motor_model.py        # Extended model with thermal effects
        │   └── pmsm_motor_model.py            # Full-order PMSM model
        │
        ├── 🔗 integration/
        │   ├── ev_digital_twin.py             # Core integration class (main model)
        │   └── enhanced_ev_digital_twin.py    # Enhanced integration with RUL
        │
        ├── 📡 simulation/
        │   ├── real_time_simulation.py        # Real-time sim engine + live plots
        │   └── reporting_dashboard.py         # Post-run analysis & report generation
        │
        ├── 🌐 web_interface/
        │   ├── index.html                     # Main live dashboard
        │   ├── launcher.html                  # Simulation launcher UI
        │   ├── parameter_setup.html           # Vehicle parameter config UI
        │   └── launch_with_parameters.py      # Web server for the dashboard
        │
        ├── 📄 data_export/                    # Auto-generated simulation CSVs
        │
        ├── 📚 docs/                           # Full technical documentation
        │
        ├── 🖥️  bat/                           # Windows one-click launchers
        │   ├── run_ev_digital_twin.bat        # ⭐ Recommended all-in-one launcher
        │   ├── start_enhanced_ev_digital_twin.bat
        │   └── start_web_interface.bat
        │
        ├── enhanced_ev_launcher.py            # Enhanced Python launcher
        ├── enhanced_real_time_simulation.py   # Standalone enhanced simulation
        ├── web_interface_launcher.py          # Web server bootstrap
        └── motor_rul.js                       # Motor RUL JS module
```

---

## Installation

### Prerequisites

| Requirement | Version |
|---|---|
| Windows | 10 or 11 (64-bit) |
| Python | 3.8 or higher |
| pip | Latest |

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/Mohammedosama111/AutoPulse_ev_digital_twin_windows.git
cd AutoPulse_ev_digital_twin_windows

# 2. (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install numpy pandas matplotlib scipy
```

---

## Usage

### Option A — One-Click Windows Launcher (Recommended)

Navigate to `ev_digital_twin_windows/ev_digital_twin/bat/` and double-click:

```
run_ev_digital_twin.bat
```

This launches the Python backend **and** opens the web dashboard in your default browser automatically.

### Option B — Python CLI

```python
from integration.ev_digital_twin import ElectricVehicleDigitalTwin
from simulation.real_time_simulation import RealTimeEVSimulation

# Build the digital twin
ev = ElectricVehicleDigitalTwin(
    battery_capacity=75.0,       # kWh
    motor_power=150.0,           # kW
    vehicle_mass=2000.0,         # kg
)

# Run real-time simulation
sim = RealTimeEVSimulation(ev_model=ev)
sim.run()
```

### Option C — Web Interface with Custom Parameters

```bash
cd ev_digital_twin_windows/ev_digital_twin
python web_interface_launcher.py
# Open http://localhost:8080 in your browser
```

---

## Configuration Parameters

| Parameter | Default | Unit | Description |
|---|---|---|---|
| `battery_capacity` | 75.0 | kWh | Total usable energy capacity |
| `battery_nominal_voltage` | 400.0 | V | Pack nominal voltage |
| `motor_power` | 150.0 | kW | Peak motor power |
| `motor_nominal_speed` | 8000.0 | rpm | Base speed (corner point) |
| `vehicle_mass` | 2000.0 | kg | Kerb weight |
| `wheel_radius` | 0.33 | m | Loaded tyre radius |
| `gear_ratio` | 9.0 | — | Motor-to-wheel gear ratio |
| `drag_coefficient` | 0.28 | — | Aerodynamic C_d |
| `frontal_area` | 2.3 | m² | Frontal cross-section |
| `rolling_resistance` | 0.01 | — | Tyre rolling resistance μ |

---

## Tech Stack

```mermaid
graph LR
    PY["Python 3.8+"] --> NP["NumPy — Numerical Arrays"]
    PY --> SP["SciPy — ODE Solvers"]
    PY --> PD["Pandas — Data I/O"]
    PY --> MPL["Matplotlib — Live Plots"]
    PY --> HTTP["http.server — Web Server"]
    WEB["Web Frontend"] --> HTML["HTML5 / CSS3"]
    WEB --> JS["JavaScript (Vanilla)"]
    JS --> CHARTS["Chart.js — Live Dashboard"]
    WIN["Windows Launchers"] --> BAT[".bat Scripts"]
    BAT --> PY
```

---

## Author

**Mohammed Osama**
- GitHub: [@Mohammedosama111](https://github.com/Mohammedosama111)
- Email: mo0441880@gmail.com

---

*Built with physics, Python, and a passion for clean energy systems.*
