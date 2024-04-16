import json
import paramiko
import logging
import tarfile
from flask import Flask, send_file
from io import BytesIO
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the configuration file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

app = Flask(__name__)

@app.route("/<compressed_file>/<filename>", methods=['GET'])
def SFTPfle(compressed_file, filename):
    sftp_config = config.get('sftp', {})
    hostname = sftp_config.get('hostname')
    port = sftp_config.get('port', 22)
    username = sftp_config.get('username')
    password = sftp_config.get('password')

    # Create a new SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the server
        client.connect(hostname, port, username, password)
        
        # Open SFTP connection
        sftp_client = client.open_sftp()

        # Construct the directory path based on the compressed_file parameter
        directory_path = sftp_config.get('directory_path')
        
        logger.info(f"Listing files in directory: {directory_path}")
        # Get list of files in the directory
        files = sftp_client.listdir(directory_path)
        logger.info(files)

        # Find the specific file with the format "month-year.tar.gz"
        file_to_download = next((f for f in files if f.endswith('.tar.gz') and f.startswith(compressed_file)), None)
        
        # If the file is found, get its contents
        if file_to_download:
            try:
                # Download the file into memory
                with BytesIO() as file_buffer:
                    sftp_client.getfo(os.path.join(directory_path, file_to_download), file_buffer)
                    file_buffer.seek(0)
                    
                    # Open the tar.gz file from memory
                    with tarfile.open(fileobj=file_buffer, mode="r:gz") as tar:
                        # Get a list of names of files in the archive
                        file_names = tar.getnames()
                        # Check if the specific file exists in the archive
                        if filename in file_names:
                            # Extract the specific file from the archive
                            specific_file = tar.extractfile(filename)
                            if specific_file:
                                # Read the contents of the specific file
                                content = specific_file.read()

                                # Save the mp3 file to a temporary file
                                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                                    temp_file.write(content)
                                    temp_file_path = temp_file.name

                                # Return the mp3 file as response
                                return send_file(temp_file_path, mimetype='audio/mpeg')
                            else:
                                return "Failed to read specific file."
                        else:
                            return "Specific file not found in archive."
            finally:
                # Close SFTP connection
                sftp_client.close()
        else:
            return "File not found."

    except FileNotFoundError as e:
        return str(e)
    except PermissionError as e:
        return str(e)
    except Exception as e:
        logger.error(str(e))
        return str(e)
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
