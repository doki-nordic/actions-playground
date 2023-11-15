# Actions Playground

Creating a GitHub Actions workflow with non-trivial commands may be annoying.
Especially, when you have to do some experiments first, e.g. what command will work or which dependencies you need.
It can be even harder when you are working on an operating system different from the target OS.
Pushing and re-running the workflow each time is a nightmare.

This repository tries to simplify this kind of work.
With it, you can start a single job that waits for your commands.
This way, you can prepare your commands for a workflow interactively without committing, pushing, and long waiting.

# Usage

First, you have to do [one-time preparation](#one-time-preparations) to setup VPN and your fork.
Next, you can [start the workflow and connect to the runner](#connecting-to-the-runner) over HTTP, SSH, RDP or VNC.
Finally, when you are connected, you can use [dedicated tools](#using-dedicated-tools-on-a-runner) to simplify
your work on the runner.

Possible connection types depends on the runner OS:

| runner OS   | HTTP| SSH | SFTP | RDP | VNC |
|-------------|-----|-----|------|-----|-----|
| **Ubuntu**  | yes | yes | yes  | no  | no  |
| **macOS**   | yes | yes | yes  | no  | yes[^1] |
| **Windows** | yes | yes | yes  | yes | no  |

[^1] - VNC server on `macos-11` is broken.
[^1]: VNC server on `macos-11` is broken.

## One-time preparations

### Setup VPN

1. Install `ZeroTier`. \
   https://www.zerotier.com/download/

1. Create your private network, if you don't have it yet. \
   https://my.zerotier.com/

1. Create a new *API Access Token*. \
   https://my.zerotier.com/account

1. Connect to your private network from your machine using GUI or the following command:
   ```
   sudo zerotier-cli join <network ID>
   ```

### Prepare your repository

1. Fork this repository on GitHub.

1. Add GitHub Actions secrets in your fork's settings:
   * `NETWORK_ID` - your private network id.
   * `ACCESS_TOKEN` - your *API Access Token* .
   * `PASSWORD` - a password that you want to use later for authentication.
   * `IP` - IP address. Make sure that it matches you virtual network
     configuration and it does not conflicts with *IPv4 Auto-Assign* or
     *IPv6 Auto-Assign* ranges or other network members.

1. Run `Generate New Keys` workflow in your fork's Actions.
   It will generate new internal keys needed for the SSH and it will check your
   configuration.

1. If you want to use certificate authentication in the SSH, you have to configure it.
   See *[Setup SSH authentication](#setup-ssh-authentication)*, for details.

## Connecting to the runner

1. Go to your fork's `Actions`, select `Playground` workflow and `Run workflow`.
   You can select which OS you want to start. For Windows, you can select
   default shell that will be available over HTTP and SSH.

1. Runner will be ready to connect after approx. 3 min, when the `Your work starts here` step is running.

1. Connect to your runner over HTTP, SSH, RDP or VNC.
   * Address: configured previously in the repository's `IP` variable/secret,
   * User name:`runner` on Ubuntu and macOS, `runneradmin` on Windows
     (user name is not needed for VNC legacy mode),
   * Password: configured previously in the repository's `PASSWORD` secret.

   For example, to connect:

   * over HTTP, type the following address to your browser:
      ```
      http://<your runner ip address>/
      ```

   * over SSH to Ubuntu or macOS runner:
     ```
     ssh runner@<your runner ip address>
     ```
     If you have a private key in a file, you can add `-i <path to private key>` option.


1. When you are done, use following command to end the action:
   ```
   exit_job
   ```

## Using dedicated tools on a runner

When you connect, SSH will show you a banner with information how to use tools
to simplify work with the runner. You may need to scroll up a bit to see it.

### macOS, Ubuntu and Windows bash banner

<!--! data/banner-bash.txt !-->
```
Hello!

You can play with the runner now.

. exit_job
    Exit current action job with success.

. load_job
    Load environment variables that are available inside job steps, for
    example variables starting with the "GITHUB_" prefix. If you are
    connecting over HTTP the environment is already loaded, you can
    skip this command.

/tmp/log
    A FIFO that redirects everything from it to the log on GitHub Action.
    For example, the following command will print bash history to log:

        history > /tmp/log

    WINDOWS ONLY: When using a bash-incompatible tools from bash shell,
    the FIFO may not work, but "\\.\pipe\log" may work instead.

$GH_ARTIFACT
    An environment variable set by ". load_job" script containing a path.
    Content of this directory will be published as a workflow artifact.
    For example, you can compress and send current directory to the artifact:

        tar -czf $GH_ARTIFACT/workspace.tgz .

    Artifact will be available only after successful finish of workflow run,
    so you have to call ". exit_job" when you're done.

ghctx
    Command outputs GitHub Actions context value. For example, show runner OS:

        ghctx runner.os

    WINDOWS ONLY: The context contains OS-compatible paths, but if you are
    using bash in Windows, you may want to convert them to bash-compatible
    paths with the "-p" option.

------------------------------------------------------------------------------
You can see more examples of commands in your bash history (up arrow key).
------------------------------------------------------------------------------
```
<!--! !-->

### Windows cmd and PowerShell banner

<!--! data/banner-cmd.txt !-->
```
Hello!

You can play with the runner now.

Currently, PowerShell is not fully supported. Some of commands below may
work only in cmd.

exit_job
    Exit current action job with success.

load_job
    Load environment variables that are available inside job steps, for
    example variables starting with the "GITHUB_" prefix. If you are
    connecting over HTTP the environment is already loaded, you can
    skip this command.

\\.\pipe\log
    A named pipe that redirects everything from it to the log on GitHub Action.
    For example, the following command will print your history to log:

        doskey /history > \\.\pipe\log

%GH_ARTIFACT%
    An environment variable set by "load_job" script containing a path.
    Content of this directory will be published as a workflow artifact.
    For example, you can compress and send current directory to the artifact:

        tar -czf %GH_ARTIFACT%\workspace.tgz .

    Artifact will be available only after successful finish of workflow run,
    so you have to call "exit_job" when you're done.

ghctx
    Command outputs GitHub Actions context value. For example, show runner OS:

        ghctx runner.os

------------------------------------------------------------------------------
```
<!--! !-->


## Setup SSH authentication

This is needed only if you want to use certificate authentication in SSH.
You can skip this, if you want to use SSH password authentication, RDP or HTTP.

You have a few options here, depending on your authentication preferences:

1. If you want to use your existing SSH public key (`*.pub`),
   e.g. from your `~/.ssh/` directory, copy its content to the `CLIENT_KEY` secret.

1. If you want to use a new SSH key that was automatically generated,
   you can go [`keys` branch](../../tree/keys) that was created by the
   `Generate New Keys` workflow. Open ZIP file using a password from
   the `PASSWORD` secret. You will have there a new private key that you can later use
   to connect over the SSH.

1. If you want to generate your own SSH key pair (e.g. using instructions from
   [Generating a new SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#generating-a-new-ssh-key)),
   you have to copy newly generated public key to the `CLIENT_KEY` secret.

1. You can combine above methods multiple times. The `CLIENT_KEY` secret
   accepts multiple public keys, one key per line.
