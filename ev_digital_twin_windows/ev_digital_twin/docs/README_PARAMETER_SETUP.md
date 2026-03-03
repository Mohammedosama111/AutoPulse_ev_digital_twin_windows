# Electric Vehicle Digital Twin - Parameter Configuration Interface

## Overview

The EV Digital Twin now includes a comprehensive parameter configuration interface that allows users to customize battery, motor, and vehicle parameters before starting the simulation. This ensures that the simulation accurately reflects the specific vehicle configuration you want to analyze.

## Features

### 🚗 Vehicle Presets
- **Sedan**: Standard passenger vehicle with balanced performance
- **SUV**: Larger vehicle with higher mass and drag coefficient
- **Sports Car**: High-performance vehicle with optimized aerodynamics
- **Commercial**: Heavy-duty vehicle with high capacity and power
- **Custom**: Configure all parameters manually

### 🔋 Battery Configuration
- **Capacity**: Total energy storage (20-200 kWh)
- **Nominal Voltage**: Pack voltage (200-800V)
- **Cell Configuration**: Series/parallel arrangement
- **Initial SOC**: Starting charge level (10-100%)
- **Initial SOH**: Battery health (70-100%)

### ⚡ Motor Configuration
- **Power**: Maximum continuous power (50-500 kW)
- **Nominal Speed**: Operating speed (3000-15000 rpm)
- **Motor Type**: PMSM, BLDC, or Induction
- **Pole Pairs**: Affects speed/torque characteristics
- **Base Efficiency**: Nominal operating efficiency

### 🚙 Vehicle Parameters
- **Mass**: Total vehicle weight
- **Drag Coefficient**: Aerodynamic efficiency
- **Frontal Area**: Cross-sectional area
- **Rolling Resistance**: Tire/road friction
- **Wheel Radius**: Affects speed calculations
- **Gear Ratio**: Transmission ratio

## How to Use

### Step 1: Launch the Interface
```bash
# Option 1: Use the batch file (Windows)
start_ev_digital_twin.bat

# Option 2: Use Python directly
python launch_with_parameters.py

# Option 3: Open manually
# Navigate to the web_interface folder and open launcher.html
```

### Step 2: Configure Parameters
1. **Choose Vehicle Type**: Select a preset or custom configuration
2. **Battery Setup**: Configure capacity, voltage, and cell arrangement
3. **Motor Setup**: Set power, speed, and efficiency parameters
4. **Vehicle Setup**: Define mass, aerodynamics, and mechanical properties

### Step 3: Start Simulation
- Click "Start Simulation" to begin with your configured parameters
- The simulation will use your custom parameters for accurate results

## File Structure

```
web_interface/
├── launcher.html                 # Main entry point
├── parameter_setup.html          # Parameter configuration interface
├── index.html                    # Main simulation dashboard
├── launch_with_parameters.py     # Python launcher script
├── start_ev_digital_twin.bat     # Windows batch launcher
├── README_PARAMETER_SETUP.md     # This file
└── [other existing files...]
```

## Parameter Validation

The interface includes real-time validation to ensure:
- ✅ Parameter values are within acceptable ranges
- ✅ Battery and motor specifications are compatible
- ✅ Vehicle parameters are realistic
- ✅ All required fields are completed

## Preset Configurations

### Sedan (Default)
- Battery: 75 kWh, 400V, 96S4P
- Motor: 150 kW, 8000 rpm
- Vehicle: 2000 kg, Cd=0.28

### SUV
- Battery: 100 kWh, 400V, 96S6P
- Motor: 200 kW, 7000 rpm
- Vehicle: 2500 kg, Cd=0.35

### Sports Car
- Battery: 85 kWh, 800V, 192S2P
- Motor: 300 kW, 12000 rpm
- Vehicle: 1800 kg, Cd=0.25

### Commercial
- Battery: 150 kWh, 600V, 144S8P
- Motor: 250 kW, 6000 rpm
- Vehicle: 3500 kg, Cd=0.45

## Technical Details

### Parameter Storage
- Parameters are stored in browser localStorage
- Configuration persists between sessions
- Can be exported/imported for sharing

### Integration
- Parameters are automatically loaded into the simulation
- Real-time updates to vehicle behavior
- Dashboard shows current configuration

### Compatibility
- Works with existing simulation models
- Backward compatible with default parameters
- No changes required to core simulation logic

## Troubleshooting

### Common Issues

1. **Parameters not loading**
   - Clear browser cache and localStorage
   - Restart the web interface
   - Check browser console for errors

2. **Simulation not starting**
   - Ensure all required parameters are set
   - Check parameter validation messages
   - Verify browser compatibility

3. **Performance issues**
   - Use recommended parameter ranges
   - Avoid extreme values that may cause instability
   - Check system resources

### Browser Compatibility
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Advanced Usage

### Custom Parameter Sets
You can create and save custom parameter configurations:
1. Configure parameters as desired
2. Use browser developer tools to export localStorage
3. Share configurations with other users

### Integration with Python Models
The web interface parameters can be exported to work with the Python simulation models:
```python
# Example: Load parameters from web interface
import json
with open('parameters.json', 'r') as f:
    params = json.load(f)
    
# Use parameters in Python simulation
ev_twin = EnhancedElectricVehicleDigitalTwin(
    battery_capacity=params['batteryCapacity'],
    motor_power=params['motorPower'],
    vehicle_mass=params['vehicleMass']
)
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review parameter validation messages
3. Consult the main project documentation
4. Check browser console for error details

---

**Version**: 2.0  
**Last Updated**: 2024  
**Compatibility**: EV Digital Twin v2.0+ 