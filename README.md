# SFTP File Download Service

This Flask application allows you to download files from an SFTP server. It provides an endpoint that accepts two parameters: `filename` (the name of the compressed file) and `specific_filename` (the name of the file you want to extract from the compressed file).

`Flask` and `Paramiko` have to be installed to work propertly

---

## Configuration File (`config.json`)

Create a `config.json` file with the following structure and fill it with the server values:

```json
{
    "sftp": {
        "hostname": "your_hostname",
        "port": your_port_number,
        "username": "your_username",
        "password": "your_password",
        "directory_path": "/your/directory/path"
    }
}

```
Replace `"your_hostname"`, `your_port_number`, `"your_username"`, `"your_password"`, and `"/your/directory/path"` with your actual server values.
