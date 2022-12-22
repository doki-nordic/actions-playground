# actions-playground

Creating a GitHub Actions workflow with non-trivial commands may be annoying.
Especially, when you have to do some experiments first, e.g. what command will work or which dependencies you need.
It can be even harder when you are working on an operating system different from the target OS.
Pushing and re-running the workflow each time is a nightmare.

This repository tries to simplify this kind of work.
With it, you can start a single job that waits for your commands.
This way, you can prepare your commands for a workflow interactively without committing, pushing, and long waiting.

## How to use it

### Preperation

1. Install `ZeroTier`. \
   https://www.zerotier.com/download/
1. Create your private network if you don't have it. \
   https://my.zerotier.com/
1. Connect to your private network from your machine using GUI or the following command:
   ```
   sudo zerotier-cli join <network ID>
   ```
1. Accept new node in your ZeroTier private network. \
   https://my.zerotier.com/
1. Fork this repository on GitHub.
1. Go to your clonned repository settings and set `PASSWORD` secret (Secrets -> Actions).
   It will be used for ZIP encryption, SSH password authentication (not supported on MacOS runners) and RDP authentication (only Windows runner).
1. Run `Generate keys` action and download encrypted ZIP from artifacts.
   You can specify number of new client keys to generate.
   They can be used to connect over SSH without typing password (required on MacOS runners).
   You can generate new ones here or you can later provide your own SSH keys, e.g. from `~/.ssh/id_*.pub` files.
1. Fill rest of the action secrets:
   * `NETWORK_ID` - Your ZeroTier netword id.
   * `IDENTITY` - ZeroTier identity key. Copy from `secrets.IDENTITY.txt` file.
   * `HOST_KEYS` - SSH server private keys. Copy from `secrets.HOST_KEYS.txt` file.
   * `CLIENT_KEYS` - SSH clients public keys. Copy from `secrets.CLIENT_KEYS.txt` file.
      You can add more client keys to the secret (one key per line).

### Connecting to the runner

1. Select OS that you want to use and run the GitHub Action on your fork.
   Only one action at a time is allowed, otherwise you will have node conflicts on your private network.
   Windows runner will allow you to select your default shell.
1. *(one time step)* Accept new node in your ZeroTier private network. \
   https://my.zerotier.com/ \
   Newly assigned IP address of the runner will be needed later. If you don't see the address immediately, wait and refresh the page.
1. Runner will be ready to connect when `Your work starts here` step is running.
1. Connect to your runner over SSH. Connection parameters:
   * **IP address**: copy form https://my.zerotier.com/
   * **Port**: 22 (default) on Windows runner, 9852 on other
   * **Login**: `runneradmin` on Windows runner, `runner` on other
   * You can choose one authentication method (macOS does not support password authentication):
     * **Password**: from your `PASSWORD` secret
     * **Client key**: use a key file associated with one of public keys provided in `CLIENT_KEYS` secret.
   For example, to connect from command line to Ubuntu runner using certificate authentication:
   ```
   ssh runner@<your runner ip address> -p 9852 -i <your client_key>
   ```
1. On Windows runner, you can use RDP. IP address, login and password the same as above.
   Don't close any windows that are aready opened there. You may loose connection with your action.
1. To end the action, use following command:
   ```
   exit_job
   ```
   Alternatively, you can use GitHub web page to cancel the action.

### Using dedicated tools on the runner

* **`exit_job`** - this command will end the action with success.
* **`job_vars`** - this script sets environment variables and changes the directory to job workspace directory.
  This is to mimmic the environment that is available for job setps. On `bash` shell, you have to source this sctipt
  i.e. call `. job_vars` or `source job_vars`.
* **`/tmp/log`** - it is a FIFO that redirects erything from it to job log on GitHub Action.
  For example, the following command with print all your `bash` history to log, so you will be able to reuse your commands later:
  ```
  history > /tmp/log
  ```
* **`\\.\pipe\log`** - this is Windows named pipe. It does the same as `/tmp/log`, but it can be used in Windows with shells and tools that does not support FIFOs.
  For example, this command will print `cmd` history to your log:
  ```
  doskey /history > \\.\pipe\log
  ```
* **`/tmp/artifact`** or **`%TEMP%\artifact`** - path to an artifact directory.
  Content of this directory will be packed and availabe for download. You can copy results of your work there, e.g.:
  ```
  cp my_file.txt /tmp/artifact/
  ```
  Artifact will be available after successfull end of job, so you have to call `exit_job`.
* **`GHCTX_***`** - environment variables set by `job_vars` script that contains GitHub Actions Contexts, e.g. `GHCTX_SECRETS_GITHUB_TOKEN`
  contains value from `${{ secrets.GITHUB_TOKEN }}`. Not all values are available. Edit `.github/workflows/action.yml` if you need more.

If you are using `bash` shell, you can see some example commands in your history (up arrow key).
