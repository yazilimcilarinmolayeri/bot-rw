# ymybot-rw
![](https://img.shields.io/badge/python-3.8%2B-blue) ![](https://img.shields.io/pypi/v/discord.py?label=discord.py) ![](https://img.shields.io/pypi/v/jishaku?label=jishaku) ![](https://img.shields.io/badge/code%20style-black-black)

## Installation and Setup
1. Clone the repository.
```shell
git clone https://github.com/yazilimcilarinmolayeri/ymybot-rw
cd ymybot-rw
```

2. Install the ymybot-rw's dependencies.
```shell
pip3 install -U -r requirements.txt
```

3. Edit a config.json file.
```shell
mv config.json.sample config.json
```

4. Setup the service file. Replace `user` with your custom username before.
```shell
cp ymybot-rw.service /etc/systemd/system/
```

5. Enable services (optionally) and start the bot.
```shell
python3 bot.py
# or
systemctl daemon-reload
systemctl enable ymybot-rw.service
systemctl start ymybot-rw.service
```

## Support
You can join the server and test the bot. Invite: https://discord.gg/KazHgb2

## License
This project is licensed under the GPL-3.0 - see the [LICENSE](LICENSE) file for details.