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
ip,username,password,command1,command2
10.0.1.36,admin,mypassword,hostname CONF-RM-101,addmaster 11 10.0.1.100
10.0.1.37,admin,mypassword,hostname CONF-RM-102,addmaster 12 10.0.1.100
10.0.1.38,admin,mypassword,hostname CONF-RM-103,addmaster 13 10.0.1.100
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

## Common Use Cases

### Initial Deployment
Set hostname and IP table on new devices:
```csv
ip,username,password,command1,command2
10.0.1.36,admin,SecurePass123,hostname CONF-RM-101,addmaster 11 10.0.1.100
10.0.1.37,admin,SecurePass123,hostname CONF-RM-102,addmaster 12 10.0.1.100
10.0.1.38,admin,SecurePass123,hostname CONF-RM-103,addmaster 13 10.0.1.100
```

### Hostname Configuration
Set hostnames across multiple devices:
```csv
ip,username,password,command1
10.0.1.36,admin,password,hostname PROC-BOARDROOM
10.0.1.37,admin,password,hostname PROC-CONF-A
10.0.1.38,admin,password,hostname PROC-CONF-B
10.0.1.39,admin,password,hostname PROC-TRAINING
```

### IP Table Setup
Configure master connections with unique IP IDs:
```csv
ip,username,password,command1,command2
10.0.1.36,admin,password,addmaster 11 10.0.1.100,addmaster 21 10.0.1.101
10.0.1.37,admin,password,addmaster 12 10.0.1.100,addmaster 22 10.0.1.101
10.0.1.38,admin,password,addmaster 13 10.0.1.100,addmaster 23 10.0.1.101
```

### Firmware Check
Verify firmware versions across all devices:
```csv
ip,username,password,command1
10.0.1.36,admin,password,ver
10.0.1.37,admin,password,ver
10.0.1.38,admin,password,ver
```

## Example Output

```
Crestron Bulk Device Setup Script - Enhanced with Dynamic Commands
================================================================
📁 Found default configuration file: devices.csv
📋 Detected 2 command columns in CSV: command1, command2
✅ Row 2: 10.0.1.36 - 2 commands loaded
✅ Row 3: 10.0.1.37 - 2 commands loaded
✅ Loaded 2 devices from configuration

📋 Deployment Configuration:
   Devices to process: 2
   Default username: admin
   Command distribution:
     2 device(s) with 2 command(s)

Proceed with deployment to 2 devices? (y/N): y

🚀 Starting bulk deployment...

[1/2] Processing 10.0.1.36...
============================================================
Processing Device: 10.0.1.36
Commands to execute: 2
  1. hostname CONF-RM-101
  2. addmaster 11 10.0.1.100
============================================================
✅ Connected to 10.0.1.36 with admin credentials
🔧 Executing 2 commands on 10.0.1.36
✅ 2/2 commands completed on 10.0.1.36
✅ Device 10.0.1.36 completed successfully

📈 Deployment Summary:
   Total devices: 2
   Successful devices: 2
   Failed devices: 0
   Device success rate: 100.0%
   Total commands executed: 4
   Successful commands: 4
   Command success rate: 100.0%

🏁 Bulk deployment completed!
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

Created by [Solution AV Automation](https://github.com/SolutionAVAutomation) for AV/IT professionals managing Crestron deployments.
