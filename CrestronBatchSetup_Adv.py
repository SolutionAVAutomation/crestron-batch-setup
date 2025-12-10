#!/usr/bin/env python3
"""
Crestron Bulk Device Setup Script - Enhanced Response Logging with Dynamic Commands
Automates setup and configuration for multiple Crestron devices with full command response logging.
Supports unlimited command columns (command1, command2, command3, etc.) from CSV files.
FIXED: Added initialization delay to resolve first command failure issue.
"""

import paramiko
import time
import sys
import logging
import csv
import re
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

class CrestronBulkManager:
    def __init__(self, config_file: str, timeout: int = 10):
        self.config_file = config_file
        self.timeout = timeout
        self.ssh_client = None
        self.shell_channel = None
        self.interactive_mode = False
        self.results = []
        
        # Setup logging with enhanced response logging
        log_filename = f"crestron_bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Create file handler
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        
        # Create console handler that we can control
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.INFO)
        self.console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        
        # Setup logger
        self.logger = logging.getLogger(f"crestron_bulk_{id(self)}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(self.console_handler)
        
        self.log_filename = log_filename
        self.logger.info(f"Starting Crestron bulk deployment session")
        print(f"📝 Logging to: {log_filename}")
    
    def extract_commands_from_row(self, row: Dict) -> List[str]:
        """Extract all command columns (command1, command2, etc.) from a CSV row."""
        commands = []
        
        # Get all keys that match the pattern 'command' followed by a number
        command_pattern = re.compile(r'^command(\d+)$', re.IGNORECASE)
        command_keys = []
        
        for key in row.keys():
            match = command_pattern.match(key.strip())
            if match:
                command_number = int(match.group(1))
                command_keys.append((command_number, key))
        
        # Sort by command number to maintain order
        command_keys.sort(key=lambda x: x[0])
        
        # Extract commands in order, skipping empty ones
        for _, key in command_keys:
            command = row[key].strip()
            if command:
                commands.append(command)
        
        return commands
    
    def load_device_config(self) -> List[Dict]:
        """Load device configuration from file with dynamic command support."""
        devices = []
        
        if not Path(self.config_file).exists():
            print(f"❌ Configuration file not found: {self.config_file}")
            return devices
        
        try:
            # Try to detect file format
            with open(self.config_file, 'r') as f:
                first_line = f.readline().strip()
                
            # Reset file pointer and read based on format
            if ',' in first_line or first_line.lower().startswith('ip'):
                # CSV format
                with open(self.config_file, 'r') as f:
                    reader = csv.DictReader(f)
                    
                    # Get header info for command detection
                    fieldnames = reader.fieldnames
                    command_columns = [col for col in fieldnames if re.match(r'^command\d+$', col.strip(), re.IGNORECASE)]
                    max_commands = len(command_columns)
                    
                    if max_commands > 0:
                        print(f"📋 Detected {max_commands} command columns in CSV: {', '.join(sorted(command_columns, key=lambda x: int(re.search(r'\\d+', x).group())))}")
                    
                    for row_num, row in enumerate(reader, 2):  # Start from 2 since header is row 1
                        # Get IP address (try different case variations)
                        ip = ''
                        for ip_key in ['ip', 'IP', 'Ip', 'iP']:
                            if ip_key in row and row[ip_key].strip():
                                ip = row[ip_key].strip()
                                break
                        
                        if not ip:
                            print(f"⚠️  Row {row_num}: No IP address found, skipping")
                            continue
                        
                        # Get username (try different case variations)
                        username = 'admin'  # default
                        for user_key in ['username', 'USERNAME', 'Username', 'user', 'USER']:
                            if user_key in row and row[user_key].strip():
                                username = row[user_key].strip()
                                break
                        
                        # Get password (try different case variations)
                        password = ''
                        for pass_key in ['password', 'PASSWORD', 'Password', 'pass', 'PASS']:
                            if pass_key in row and row[pass_key].strip():
                                password = row[pass_key].strip()
                                break
                        
                        # Extract all commands dynamically
                        commands = self.extract_commands_from_row(row)
                        
                        device_config = {
                            'ip': ip,
                            'username': username,
                            'password': password,
                            'commands': commands
                        }
                        
                        devices.append(device_config)
                        
                        if commands:
                            print(f"✅ Row {row_num}: {ip} - {len(commands)} commands loaded")
                        else:
                            print(f"ℹ️  Row {row_num}: {ip} - No commands specified")
                            
            else:
                # Simple text format - one IP per line
                with open(self.config_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            devices.append({
                                'ip': line,
                                'username': 'admin',
                                'password': '',  # Will be prompted
                                'commands': []   # Will be prompted
                            })
                            
        except Exception as e:
            print(f"❌ Error reading configuration file: {e}")
            return []
            
        print(f"✅ Loaded {len(devices)} devices from configuration")
        return devices
    
    def connect_with_defaults(self, host: str) -> bool:
        """Try to connect with Crestron default credentials."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=host,
                port=22,
                username="Crestron",
                password="",
                timeout=5,
                look_for_keys=False,
                allow_agent=False
            )
            
            self.shell_channel = self.ssh_client.invoke_shell(term='vt100', width=80, height=24)
            self.shell_channel.settimeout(self.timeout)
            return True
            
        except Exception as e:
            self.logger.info(f"Default connection to {host} failed: {e}")
            return False
    
    def connect_with_auth(self, host: str, username: str, password: str) -> bool:
        """Connect with provided credentials."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=host,
                port=22,
                username=username,
                password=password,
                timeout=5,
                look_for_keys=False,
                allow_agent=False
            )
            
            self.shell_channel = self.ssh_client.invoke_shell(term='vt100', width=80, height=24)
            self.shell_channel.settimeout(self.timeout)
            return True
            
        except Exception as e:
            self.logger.info(f"Auth connection to {host} failed: {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection."""
        if self.shell_channel:
            self.shell_channel.close()
            self.shell_channel = None
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
    
    def send_command(self, command: str, delay: float = 0.5):
        """Send command to device."""
        if not self.shell_channel:
            raise Exception("Not connected to device")
        
        self.logger.info(f"SEND: {repr(command.encode())}")
        self.shell_channel.send(command)
        time.sleep(delay)
    
    def receive_data(self, timeout: Optional[float] = None) -> str:
        """Receive data from device."""
        if not self.shell_channel:
            raise Exception("Not connected to device")
        
        if timeout:
            original_timeout = self.shell_channel.gettimeout()
            self.shell_channel.settimeout(timeout)
        
        try:
            if self.shell_channel.recv_ready():
                data = self.shell_channel.recv(1024).decode('utf-8', errors='ignore')
                self.logger.info(f"RECV: {repr(data.encode())}")
                return data
            else:
                return ""
        except Exception as e:
            self.logger.info(f"RECV error: {e}")
            return ""
        finally:
            if timeout:
                self.shell_channel.settimeout(original_timeout)
    
    def wait_for_prompt(self, expected_text: str, max_wait: int = 10) -> bool:
        """Wait for specific prompt."""
        start_time = time.time()
        received_data = ""
        
        while time.time() - start_time < max_wait:
            try:
                if self.shell_channel.recv_ready():
                    data = self.shell_channel.recv(1024).decode('utf-8', errors='ignore')
                    self.logger.info(f"RECV: {repr(data.encode())}")
                    received_data += data
                    
                    if expected_text.lower() in received_data.lower():
                        return True
                
                time.sleep(0.1)
                    
            except Exception as e:
                self.logger.info(f"Error waiting for prompt: {e}")
                break
                
        self.logger.info(f"Timeout waiting for: {expected_text}")
        return False
    
    def create_admin_account(self, username: str, password: str) -> bool:
        """Create administrator account during initial setup."""
        self.logger.info(f"Creating admin account: {username}")
        
        # Send initial CR to trigger prompts
        self.send_command('\r\n')
        time.sleep(1)
        
        # Check for setup prompts
        initial_data = ""
        for _ in range(5):
            if self.shell_channel.recv_ready():
                data = self.shell_channel.recv(1024).decode('utf-8', errors='ignore')
                self.logger.info(f"RECV: {repr(data.encode())}")
                initial_data += data
            time.sleep(1)
        
        if not any(indicator in initial_data.lower() for indicator in 
                  ["create a local administrator", "username:", "please create"]):
            self.logger.info("No setup prompt found")
            return False
        
        # Wait for username prompt (it should already be there)
        if "username:" not in initial_data.lower():
            if not self.wait_for_prompt("Username:", max_wait=5):
                self.send_command('\r\n')
                if not self.wait_for_prompt("Username:", max_wait=5):
                    return False
        
        # Send username
        self.send_command(f'{username}\r\n')
        
        # Wait for password prompt
        if not self.wait_for_prompt("Password:", max_wait=5):
            return False
        
        # Send password
        self.send_command(f'{password}\r\n')
        
        # Wait for password verification
        if not self.wait_for_prompt("Verify password:", max_wait=5):
            return False
        
        # Send password verification
        self.send_command(f'{password}\r\n')
        
        # Wait for success
        if self.wait_for_prompt("successfully created", max_wait=15):
            self.logger.info("Admin account created successfully")
            return True
        else:
            self.logger.info("Failed to create admin account")
            return False
    
    def execute_commands(self, commands: List[str], host: str) -> List[Dict]:
        """Execute list of commands and return detailed responses."""
        command_results = []
        
        # CRITICAL FIX: Wait for CLI to fully initialize after connection
        time.sleep(3)  # Give device time to initialize CLI
        
        for cmd_index, command in enumerate(commands, 1):
            if not command.strip():
                continue
                
            self.logger.info(f"Executing command {cmd_index}/{len(commands)} on {host}: {command}")
            
            # Send command
            self.send_command(f'{command}\r\n')
            
            # Wait for response - collect all data over multiple receive cycles
            response_data = ""
            response_complete = False
            
            # First, wait a moment for command to execute
            time.sleep(0.5)
            
            # Collect response over several cycles
            for cycle in range(20):  # Up to 10 seconds
                if self.shell_channel.recv_ready():
                    try:
                        data = self.shell_channel.recv(2048).decode('utf-8', errors='ignore')
                        if data:
                            response_data += data
                            self.logger.info(f"RECV (cmd {cmd_index}): {repr(data.encode())}")
                            
                            # Check if we got a command prompt back (indicates completion)
                            if '>' in data and (host.upper() in data.upper() or 'crestron' in data.lower()):
                                response_complete = True
                                break
                                
                    except Exception as e:
                        self.logger.info(f"Error receiving data for command {cmd_index}: {e}")
                        break
                
                time.sleep(0.5)  # Wait between cycles
                
                # If no new data for several cycles, assume command completed
                if not self.shell_channel.recv_ready():
                    no_data_cycles = getattr(self, f'_no_data_cycles_{cmd_index}', 0) + 1
                    setattr(self, f'_no_data_cycles_{cmd_index}', no_data_cycles)
                    if no_data_cycles >= 3:  # 1.5 seconds of no data
                        response_complete = True
                        break
                else:
                    setattr(self, f'_no_data_cycles_{cmd_index}', 0)
            
            # Clean up the response
            clean_response = self.clean_command_response(response_data, command)
            
            # Log the cleaned response for easier reading
            if clean_response:
                self.logger.info(f"COMMAND OUTPUT ({host} - {command}):\n{clean_response}")
            else:
                self.logger.info(f"No response received for command: {command}")
            
            command_results.append({
                'command': command,
                'raw_response': response_data,
                'clean_response': clean_response,
                'success': bool(clean_response),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # Brief pause between commands
            time.sleep(0.5)
            
        return command_results
    
    def clean_command_response(self, raw_response: str, command: str) -> str:
        """Clean up command response for better readability."""
        if not raw_response:
            return ""
        
        lines = raw_response.split('\r\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines and command echo
            line = line.strip()
            if line and line != command and not line.endswith('>'):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines) if cleaned_lines else ""
    
    def setup_single_device(self, device_config: Dict) -> Dict:
        """Setup a single device according to configuration."""
        host = device_config['ip']
        username = device_config['username']
        password = device_config['password']
        commands = device_config['commands']
        
        result = {
            'ip': host,
            'status': 'Failed',
            'message': '',
            'setup_needed': False,
            'command_results': [],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"\n{'='*60}")
        print(f"Processing Device: {host}")
        if commands:
            print(f"Commands to execute: {len(commands)}")
            for i, cmd in enumerate(commands, 1):
                print(f"  {i}. {cmd}")
        print(f"{'='*60}")
        
        try:
            # Step 1: Try default credentials first
            if self.connect_with_defaults(host):
                print(f"✅ Connected to {host} with Crestron defaults")
                
                # Check if setup is needed
                if self.create_admin_account(username, password):
                    result['setup_needed'] = True
                    result['message'] = 'Setup completed'
                    print(f"✅ Admin account created on {host}")
                else:
                    result['message'] = 'Setup failed or not needed'
                    print(f"⚠️  Setup not completed on {host}")
                
                self.disconnect()
                time.sleep(2)  # Wait for device to be ready
            
            # Step 2: Connect with admin credentials
            if self.connect_with_auth(host, username, password):
                print(f"✅ Connected to {host} with admin credentials")
                
                # Execute post-setup commands with detailed logging
                if commands:
                    print(f"🔧 Executing {len(commands)} commands on {host}")
                    command_results = self.execute_commands(commands, host)
                    result['command_results'] = command_results
                    
                    # Count successful commands
                    successful_commands = len([r for r in command_results if r['success']])
                    print(f"✅ {successful_commands}/{len(commands)} commands completed on {host}")
                
                result['status'] = 'Success'
                print(f"✅ Device {host} completed successfully")
                
            else:
                result['message'] = 'Failed to connect with admin credentials'
                print(f"❌ Failed to connect to {host} with admin credentials")
            
        except Exception as e:
            result['message'] = f'Exception: {str(e)}'
            print(f"❌ Error processing {host}: {e}")
            
        finally:
            self.disconnect()
            
        return result
    
    def generate_report(self, results: List[Dict]):
        """Generate a comprehensive summary report."""
        report_file = f"crestron_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(report_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['IP Address', 'Status', 'Setup Needed', 'Commands Executed', 'Successful Commands', 'Message', 'Timestamp'])
            
            for result in results:
                command_results = result.get('command_results', [])
                total_commands = len(command_results)
                successful_commands = len([r for r in command_results if r['success']])
                
                writer.writerow([
                    result['ip'],
                    result['status'],
                    'Yes' if result['setup_needed'] else 'No',
                    total_commands,
                    successful_commands,
                    result['message'],
                    result['timestamp']
                ])
        
        # Generate detailed command report
        command_report_file = f"crestron_command_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(command_report_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['IP Address', 'Command', 'Success', 'Response Length', 'Timestamp'])
            
            for result in results:
                for cmd_result in result.get('command_results', []):
                    writer.writerow([
                        result['ip'],
                        cmd_result['command'],
                        'Yes' if cmd_result['success'] else 'No',
                        len(cmd_result['clean_response']),
                        cmd_result['timestamp']
                    ])
        
        print(f"\n📊 Reports saved:")
        print(f"   - Summary: {report_file}")
        print(f"   - Commands: {command_report_file}")
        
        # Summary statistics
        total = len(results)
        successful = len([r for r in results if r['status'] == 'Success'])
        setup_needed = len([r for r in results if r['setup_needed']])
        
        # Command statistics
        all_commands = []
        for result in results:
            all_commands.extend(result.get('command_results', []))
        
        total_commands = len(all_commands)
        successful_commands = len([c for c in all_commands if c['success']])
        
        print(f"\n📈 Deployment Summary:")
        print(f"   Total devices: {total}")
        print(f"   Successful devices: {successful}")
        print(f"   Failed devices: {total - successful}")
        print(f"   Required setup: {setup_needed}")
        print(f"   Device success rate: {(successful/total*100):.1f}%")
        print(f"   Total commands executed: {total_commands}")
        print(f"   Successful commands: {successful_commands}")
        if total_commands > 0:
            print(f"   Command success rate: {(successful_commands/total_commands*100):.1f}%")

def create_sample_config():
    """Create sample configuration files with multiple commands."""
    
    # Create CSV sample with multiple commands
    csv_sample = """ip,username,password,command1,command2,command3,command4,command5
10.0.1.36,admin,mypassword,ipconfig,ver,hostname,uptime,whoami
10.0.1.37,admin,mypassword,ipconfig,ver,hostname,,
10.0.1.38,admin,mypassword,ipconfig,ver,hostname,uptime,whoami
10.0.1.39,admin,mypassword,ver,hostname,,, 
10.0.1.40,admin,mypassword,ipconfig,ver,hostname,uptime,"""
    
    with open('devices_sample.csv', 'w') as f:
        f.write(csv_sample)
    
    # Create simple text sample
    txt_sample = """# Crestron Device IP Addresses
# One IP per line, lines starting with # are ignored
# Commands will be prompted interactively for this format
10.0.1.36
10.0.1.37
10.0.1.38
10.0.1.39
10.0.1.40"""
    
    with open('devices_sample.txt', 'w') as f:
        f.write(txt_sample)
    
    print("📄 Sample configuration files created:")
    print("   - devices_sample.csv (CSV format with up to 5 commands per device)")
    print("   - devices_sample.txt (Simple IP list)")
    print("\n📋 CSV Format Features:")
    print("   • Supports unlimited command columns (command1, command2, command3, etc.)")
    print("   • Empty command cells are automatically skipped")
    print("   • Commands are executed in numerical order")
    print("   • Different devices can have different numbers of commands")

def find_default_config_file():
    """Look for default configuration files in current directory."""
    # Priority order for default files
    default_files = ['devices.csv', 'devices.txt', 'crestron_devices.csv', 'config.csv']
    
    for filename in default_files:
        if Path(filename).exists():
            return filename
    
    return None

def main():
    print("Crestron Bulk Device Setup Script - Enhanced with Dynamic Commands")
    print("================================================================")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create-sample':
        create_sample_config()
        return
    
    # Look for default configuration file first
    default_config = find_default_config_file()
    
    if default_config:
        print(f"📁 Found default configuration file: {default_config}")
        use_default = input(f"Use '{default_config}'? (Y/n): ").strip().lower()
        if use_default == 'n':
            config_file = input("Enter configuration file path: ").strip()
        else:
            config_file = default_config
    else:
        # Configuration
        config_file = input("Enter configuration file path (or press Enter for 'C:\\Files\\Crestron\\devices.csv'): ").strip()
        if not config_file:
            config_file = 'C:\\Files\\Crestron\\devices.csv'
    
    if not Path(config_file).exists():
        print(f"❌ Configuration file not found: {config_file}")
        print("Run with --create-sample to create sample configuration files")
        return
    
    # Initialize bulk manager
    manager = CrestronBulkManager(config_file)
    devices = manager.load_device_config()
    
    if not devices:
        print("❌ No devices loaded from configuration file")
        return
    
    # Get common settings if not specified in config
    first_device = devices[0]
    if not first_device['password']:
        default_password = input("Enter default admin password for devices: ").strip()
        for device in devices:
            if not device['password']:
                device['password'] = default_password
    
    # For text files, get commands interactively
    if not first_device['commands']:
        print("\nEnter commands to execute on each device after setup:")
        commands = []
        for i in range(1, 11):  # Allow up to 10 commands
            cmd = input(f"Command {i} (or press Enter to finish): ").strip()
            if not cmd:
                break
            commands.append(cmd)
        
        if commands:
            for device in devices:
                if not device['commands']:
                    device['commands'] = commands.copy()
    
    # Show command summary
    command_counts = {}
    for device in devices:
        count = len(device['commands'])
        command_counts[count] = command_counts.get(count, 0) + 1
    
    # Confirmation
    print(f"\n📋 Deployment Configuration:")
    print(f"   Devices to process: {len(devices)}")
    print(f"   Default username: {first_device['username']}")
    
    # Show command distribution
    if command_counts:
        print(f"   Command distribution:")
        for count, num_devices in sorted(command_counts.items()):
            print(f"     {num_devices} device(s) with {count} command(s)")
    
    # Show sample commands if any
    if first_device['commands']:
        print(f"   Sample commands (from first device):")
        for i, cmd in enumerate(first_device['commands'][:3], 1):  # Show first 3
            print(f"     {i}. {cmd}")
        if len(first_device['commands']) > 3:
            print(f"     ... and {len(first_device['commands']) - 3} more")
    
    confirm = input(f"\nProceed with deployment to {len(devices)} devices? (y/N): ")
    if confirm.lower() != 'y':
        print("Deployment cancelled")
        return
    
    # Execute bulk deployment
    print(f"\n🚀 Starting bulk deployment...")
    results = []
    
    try:
        for i, device in enumerate(devices, 1):
            print(f"\n[{i}/{len(devices)}] Processing {device['ip']}...")
            result = manager.setup_single_device(device)
            results.append(result)
            
            # Brief pause between devices
            if i < len(devices):
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n\n⏹️  Deployment interrupted by user")
    
    # Generate comprehensive reports
    manager.generate_report(results)
    print(f"\n🏁 Bulk deployment completed!")

if __name__ == "__main__":
    main()
