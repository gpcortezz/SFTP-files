import json
import paramiko
import logging
import tarfile
from flask import Flask, send_file, jsonify
from io import BytesIO
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure error logging to a file
error_handler = logging.FileHandler('error.log')
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)
logger.addHandler(error_handler)

# Load the configuration file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

app = Flask(__name__)

@app.route("/<compressed_file>/<filename>", methods=['GET'])
def SFTPfle(compressed_file, filename):
    sftp_config = config.get('sftp', {})
    host = sftp_config.get('host')
    port = sftp_config.get('port', 22)
    username = sftp_config.get('username')
    password = sftp_config.get('password')
    directory_path = sftp_config.get('directory_path')

    # Create a new SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the server
        client.connect(host, port, username, password)

        # Open SFTP connection
        sftp_client = client.open_sftp()

        logger.info(f"Listing files in directory: {directory_path}")
        # Get list of files in the directory
        files = sftp_client.listdir(directory_path)
        logger.info(files)

        # Find the specific file with the format "month-year.tar.gz"
        file_to_download = next((f for f in files if f.endswith('.tar.gz') and f.startswith(compressed_file)), None)

        # If the file is found, get its contents
        if file_to_download:
            with BytesIO() as file_buffer:
                sftp_client.getfo(os.path.join(directory_path, file_to_download), file_buffer)
                file_buffer.seek(0)

                with tarfile.open(fileobj=file_buffer, mode="r:gz") as tar:
                    file_names = tar.getnames()
                    if filename in file_names:
                        specific_file = tar.extractfile(filename)
                        if specific_file:
                            content = specific_file.read()

                            # Return the file directly from memory
                            return send_file(
                                BytesIO(content),
                                download_name=filename,
                                mimetype='audio/mpeg'
                            )
                        else:
                            return jsonify({"error": "Failed to read specific file."}), 500
                    else:
                        return jsonify({"error": "Specific file not found in archive."}), 404
        else:
            return jsonify({"error": "File not found."}), 404
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError: { directory_path } not found.")
        return jsonify({"error": str(e)}), 404
    except PermissionError as e:
        logger.error(f"PermissionError: {e}")
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        logger.error(f"Exception: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'sftp_client' in locals():
            sftp_client.close()
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
