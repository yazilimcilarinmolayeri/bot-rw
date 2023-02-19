# bot-rw
![](https://img.shields.io/badge/python-3.8%2B-blue) ![](https://img.shields.io/pypi/v/discord.py?label=discord.py) ![](https://img.shields.io/pypi/v/jishaku?label=jishaku) ![](https://img.shields.io/badge/code%20style-black-black)

Customizable and multifunctional rewritten Discord bot for YMY. Invite: https://discord.gg/KazHgb2

## Installation and Setup
1. Clone the repository.
```shell
git clone https://github.com/yazilimcilarinmolayeri/bot-rw && cd bot-rw
```

2. Install the bot-rw's dependencies.
```shell
pip3 install --user -r requirements.txt --upgrade
```

3. Edit a config.ini file.
```shell
cp config.ini.sample config.ini
```

5. Run the bot.
```shell
python3 run.py
```

### Optionally

1. Or setup the service file. Replace `user` with your custom username before.
```shell
mv bot-rw.service.example bot-rw.service
cp bot-rw.service /etc/systemd/system/
```

2. And enable services and start. 
```shell
systemctl daemon-reload
systemctl enable bot-rw.service
systemctl start bot-rw.service
```

## License
This project is licensed under the GPL-3.0 - see the [LICENSE](LICENSE) file for details.
