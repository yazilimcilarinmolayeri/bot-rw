# ymybot-rw
![](https://img.shields.io/badge/python-3.7%2B-blue)
![](https://img.shields.io/pypi/v/discord.py?label=discord.py)
![](https://img.shields.io/pypi/v/jishaku?label=jishaku)
![](https://img.shields.io/badge/code%20style-black-black)
![](https://discord.com/api/guilds/418887354699350028/embed.png)

Hello! I am a multifunctional Discord bot (ymybot rewrite version)
> API's, Info, Owner, Utility and more...

## Installation and Setup

1. Clone the repository:
```
$ git clone https://github.com/yazilimcilarinmolayeri/ymybot-rw
$ cd ymybot-rw/
```

2. Create a virtual environment (optionally):
```
$ pip3 install -r dev-requirements.txt
$ virtualenv .venv
$ source .venv/bin/activate
```

3. Install the ymybot-rw's dependencies:
```
pip3 install -r requirements.txt
```

4. Create a config.cfg file: <br/>
Sample file: https://gist.github.com/ccctux/de1f8c8c94ab5efa754ac26ada6fca32
```
$ touch config.cfg
```

5. Setup the service file: <br/>
Replace `user` with your custom username before.
```
$ [sudo] cp ymybot-rw.service /etc/systemd/system/
```

6. Enable services (optionally) and start the bot:
```
$ [sudo] systemctl daemon-reload
$ [sudo] systemctl enable ymybot.service
$ [sudo] systemctl start ymybot.service
# or
$ python3 bot.py
```

## Support
You can join the server and test the bot. Invite: https://discord.gg/KazHgb2

## License
This project is licensed under the GPL-3.0 - see the [LICENSE](LICENSE) file for details.