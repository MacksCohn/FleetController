# TO USE
1. 
> use AWS configure command, giving it a key id, secret access key, region (us-east-2), and output format (json)
```bash
aws configure
```
2.
> pip install the requirements in a virtual environment
```bash
python3.13 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```
3.
> setup .env file with slack app information
```bash
SECRET=YOUR_APP_SECRET # should be alphanumeric
TOKEN=YOUR_APP_TOKEN   # should have xoxb-numbers-numbers-letters
SECRET=YOUR_APP_SECRET # should have xapp-num-numbers-alphanumeric
```
4. run ./start.sh while in the directory, or just source the venv and then run the script
