# Actions Playground

Creating a GitHub Actions workflow with non-trivial commands may be annoying.
Especially, when you have to do some experiments first, e.g. what command will work or which dependencies you need.
It can be even harder when you are working on an operating system different from the target OS.
Pushing and re-running the workflow each time is a nightmare.

This repository tries to simplify this kind of work.
With it, you can start a single job that waits for your commands.
This way, you can prepare your commands for a workflow interactively without committing, pushing, and long waiting.

# TL;DR

The following procedure allows you to use just remote terminal connected to Action Runner.
If you need something more, skip this chapter and see details below.

One-time setup:

1. Create your fork of this repository on GitHub.
1. Go to your fork's `Settings` and create new repository secret named `PASSWORD`
   containing password that you want to use to authenticate. Use strong password.
1. Run `Generate New Keys` workflow in your fork's Actions.

Each time you want play with the Actions:

1. Run `Playground` workflow in your fork's Actions, select `localhost.run` as the tunneling serice.
1. Go to [Wiki](../../wiki) of your fork.
1. You will see a page containing link to your terminal.
   Wait and refresh the page if it is not ready yet,
1. Connect using password that you set before in the `PASSWORD` secret.
1. Play with the Actions.
1. Finally, run `exit_job` command to terminate the Action with success.

# Features

After you setup and start an action, you will have multiple access methods available:

* **Shell over HTTP** - use your browser as remote terminal.
* **File Browser over HTTP** - use your browser to access remote file system.
* **SSH/SFTP** - secure shell and file transfer.
* **RDP** - remote desktop (Windows runners only).
* **VNC** - remote desktop (macOS runners only, VNC server on `macos-11` is broken).

# Setup

## 1. Choose and prepare tunneling method

Action runner is not visible publically over the internet.
We have to use some method of tunneling or VPN.
There is no perfect solution how to do it, so you have multiple options available.
Choose whatever suits you the best.

The following table shows free plans capabilities.
Paid plans may have less restrictions.

Feature | [pinggy.io](http://pinggy.io/) | [zrok.io](http://zrok.io) | [ZeroTier](https://www.zerotier.com/) | [localhost.run](http://localhost.run)
--------|:---------:|:-------:|:--------:|:------------:
HTTP shell | :+1: | :+1: | :+1: | :+1:
HTTP file browser | :+1: | :+1: | :+1: | :x:
SSH/RDP/VNC connections | :+1: | :+1: | :+1: | :x:
Access without account | :+1: | :x: | :x: | :+1:
Permanent address | :x: <sup>1</sup> | ?? | :+1: | :+1:/:x: <sup>2</sup>
Unlimited connection time | :x: 60 min | :+1: | :+1: | :+1:
Access without dedicated software<br/>on the client side | :+1: | :+1:/:x: <sup>3</sup> | :x: | :+1:
VPN | :x: | :x: | :+1: | :x:

<sup>1</sup> - With pinggy.io free plan, connection will be interrupted and address will change **every 60 min**.<br/>
<sup>2</sup> - If you create an accont on localhost.run and you will put an SSH keys there, you will get random permanent addresses.<br/>
<sup>3</sup> - SSH, SFTP, RDP and VNC connections require dedicated zrok.io software on the client side.

The action can use one more method called **`pinggy.io + localhost.run`**.
It uses **`localhost.run`** for HTTP shell and **`pinggy.io`** for all the other connections.

Go to setup instructions for one or more tunelling methods that you want to use:
* [**pinggy.io**](docs/pinggy.io.md)
* [**zrok.io**](docs/zrok.io.md)
* [**ZeroTier**](docs/zerotier.md)
* [**localhost.run**](docs/localhost.run.md)

## 2. Prepare your repository

1. Create your fork of this repository on GitHub.

1. Add GitHub Actions secrets and variables in your fork's settings:

   * `PASSWORD` secret - a password that you want to use later for an authentication.
     Use strong password.

   * only for pinggy.io:
      * `PINGGY_IO_TOKEN` secret - token from your pinggy.io account.

   * only for zrok.io:
      * `ZROK_IO_TOKEN` secret - token from your zrok.io account.

   * only for ZeroTier:
      * `ZEROTIER_NETWORK_ID` secret - your private network id.
      * `ZEROTIER_ACCESS_TOKEN` secret - your ZeroTier *API Access Token* .
      * `ZEROTIER_IP` variable - IP address. Make sure that it matches you virtual network
        configuration and it does not conflicts with *IPv4 Auto-Assign* or
        *IPv6 Auto-Assign* ranges or other network members.

1. Run `Generate New Keys` workflow in your fork's Actions.
   It will generate new internal keys needed for the SSH and it will check your
   configuration.

Optional tasks:

* If you want to use certificate authentication in the SSH, you have to configure it.
  See *[SSH authentication](docs/ssh.md)*, for details.

* If you want to use permanent addresses with localhost.run, see 
  [*localhost.run account setup*](docs/localhost.run.account.md).

# Usage

## 1. Connect to the runner

1. Go to your fork's `Actions`, select `Playground` workflow and `Run workflow` button.
   You can select which OS to start and which tunneling method to use. For Windows, you can also select
   default shell.

1. Runner will be ready to connect after approx. 3 min, when the `Your work starts here` step is running.

1. Go to [Wiki](../../wiki) of your fork.
   You will see there a page named as id of the Action Run that you started above.
   In it, you will see details how to connect to each available prtocol.

   The action will update this page if some information have changed, e.g. free pinggy.io connection reached 60 min limit.
   Refresh this page manually to see updated information if needed.

1. When you are done, use following command to end the action run:
   ```
   exit_job
   ```

## 2. Using dedicated tools on a runner

When you connect, SSH will show you a banner with information how to use tools
to simplify work with the runner. On some clients, you may need to scroll up a bit to see it.

You can also see the banner here:
* [bash banner](docs/bash-banner.md)
* [cmd and PowerShell banner](docs/cmd-banner.md)
