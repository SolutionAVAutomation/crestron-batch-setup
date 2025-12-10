# Crestron Batch Setup Tool

Python tool for bulk configuration and setup of Crestron devices via SSH. Automates initial admin account creation and batch command execution across multiple devices.

## Features

- **Bulk Device Setup**: Configure dozens or hundreds of Crestron devices in one run
- **Initial Setup Automation**: Automatically creates admin accounts on factory-fresh devices
- **Dynamic Commands**: Support for unlimited commands per device via CSV
- **Flexible Configuration**: CSV or simple text file formats
- **Comprehensive Logging**: Full command/response logging for troubleshooting
- **Detailed Reports**: CSV reports of deployment status and command results

## Requirements

```bash
pip install paramiko
```

## Quick Start

### 1. Create Sample Configuration Files

```bash
python CrestronBatchSetup_Adv.py --create-sample
```

This creates:
- `devices_sample.csv` - CSV format with multiple commands
- `devices_sample.txt` - Simple IP list format

### 2. Edit Your Configuration

**CSV Format** (recommended for different commands per device):
```csv
ip,username,password,command1,command2,command3,command4,command5
10.0.1.36,admin,mypassword,hostname device1,ipconfig,ver,,
10.0.1.37,admin,mypassword,hostname device2,ipconfig,ver,,
10.0.1.38,admin,mypassword,hostname device3,ipconfig,ver,uptime,
```

**Text Format** (for same commands on all devices):
```
# One IP per line
10.0.1.36
10.0.1.37
10.0.1.38
```

### 3. Run the Tool

```bash
python CrestronBatchSetup_Adv.py
```

## Configuration Options

### CSV Columns

| Column | Required | Description |
|--------|----------|-------------|
| `ip` | Yes | Device IP address |
| `username` | No | Admin username (default: `admin`) |
| `password` | No | Admin password (prompted if not provided) |
| `command1`, `command2`, ... | No | Commands to execute (unlimited columns) |

### Command Columns

- Supports unlimited command columns: `command1`, `command2`, `command3`, etc.
- Empty cells are automatically skipped
- Commands execute in numerical order
- Different devices can have different numbers of commands

## How It Works

1. **Connection Attempt**: Tries default Crestron credentials (`Crestron` / empty password)
2. **Initial Setup**: If device is factory-fresh, creates the admin account
3. **Reconnection**: Connects with the new admin credentials
4. **Command Execution**: Runs all configured commands with response logging
5. **Reporting**: Generates CSV reports of results

## Output Files

Each run generates:

- `crestron_bulk_YYYYMMDD_HHMMSS.log` - Detailed session log
- `crestron_deployment_report_YYYYMMDD_HHMMSS.csv` - Device status summary
- `crestron_command_details_YYYYMMDD_HHMMSS.csv` - Command-level results

## Example Output

```
Crestron Bulk Device Setup Script - Enhanced with Dynamic Commands
================================================================
📁 Found default configuration file: devices.csv
📋 Detected 5 command columns in CSV: command1, command2, command3, command4, command5
✅ Row 2: 10.0.1.36 - 3 commands loaded
✅ Row 3: 10.0.1.37 - 3 commands loaded
✅ Loaded 2 devices from configuration

📋 Deployment Configuration:
   Devices to process: 2
   Default username: admin
   Command distribution:
     2 device(s) with 3 command(s)

Proceed with deployment to 2 devices? (y/N): y

🚀 Starting bulk deployment...

[1/2] Processing 10.0.1.36...
============================================================
Processing Device: 10.0.1.36
Commands to execute: 3
  1. hostname device1
  2. ipconfig
  3. ver
============================================================
✅ Connected to 10.0.1.36 with admin credentials
🔧 Executing 3 commands on 10.0.1.36
✅ 3/3 commands completed on 10.0.1.36
✅ Device 10.0.1.36 completed successfully

📈 Deployment Summary:
   Total devices: 2
   Successful devices: 2
   Failed devices: 0
   Device success rate: 100.0%
   Total commands executed: 6
   Successful commands: 6
   Command success rate: 100.0%

🏁 Bulk deployment completed!
```

## Common Use Cases

### Initial Deployment
Set up hostnames, network config, and security settings on new devices:
```csv
ip,username,password,command1,command2,command3
10.0.1.36,admin,SecurePass123,hostname CONF-RM-101,dhcp,authentication on
10.0.1.37,admin,SecurePass123,hostname CONF-RM-102,dhcp,authentication on
```

### Firmware Check
Verify firmware versions across all devices:
```csv
ip,username,password,command1
10.0.1.36,admin,password,ver
10.0.1.37,admin,password,ver
10.0.1.38,admin,password,ver
```

### Network Audit
Gather network configuration from all devices:
```csv
ip,username,password,command1,command2
10.0.1.36,admin,password,ipconfig,hostname
10.0.1.37,admin,password,ipconfig,hostname
```

## Troubleshooting

### First Command Fails
The script includes a 3-second initialization delay after connection. If you still experience issues, the delay can be adjusted in the `execute_commands()` method.

### Connection Timeouts
Default timeout is 10 seconds. Adjust in the `CrestronBulkManager` constructor if needed for slower networks.

### Authentication Failures
- Verify credentials in your CSV
- Check if device has been previously configured
- Ensure SSH is enabled on the device

## License

MIT License - feel free to use and modify.

## Author

Created for AV/IT professionals managing Crestron deployments.
