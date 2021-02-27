# How to Start

## Need to download and install
- [StarCraft II](https://us.battle.net/account/download/?show=sc2&starter=sc2) (ver Starter patched 3.18.0)

- [sc2client-proto](https://github.com/Blizzard/s2client-proto) By Blizzard (ver 1.0)

- [protobuf](https://github.com/google/protobuf/releases) By google (ver 3.4.0)

First of all, Install `protobuf` from the above link.
If it sets successfully, you can check `protoc` compiler is on your machine. After that, download s2client-proto and also install it.
you may do it with command `python setup.py install`.
Now you can import `s2clientprotocol` python moudle everywhere.

## How To launch StarCraft II
To develop and check repeatedly, we need to know how to launch StarCraft II application without login with an individual account. So, we are going to use SC2switcher which is in the Support folder.

Generally you can find SC2switcher in the following path.

- On Windows
``

- On MacOSX
`/Applications/StarCraft\ II/Support/SC2Switcher.app/Contents/MacOS/SC2Switcher`

If you tried typing the path on your _cmd_ or _terminal_, you might see the login screen in StarCraft II application. It is also not proper to get any messages through the api. 

Next step is to execute StarCraft II with the specific listening port. This work is needed to communicate between our program and StarCraft II through the api.

This is not hard work. Just attach the `listen` and `port` option. We are going to communicate between the two program which are on same machine. Therefore, Just type the following options.

`--listen 127.0.0.1 --port 5000`

Then, It's done. Assemble the two parts. Like this,

`/Applications/StarCraft\ II/Support/SC2Switcher.app/Contents/MacOS/SC2Switcher --listen 127.0.0.1 --port 5000`

Now, you can see the black screen with changed mouse pointer. Great Job!
