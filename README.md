# actions-playground

Creating a GitHub Actions workflow with non-trivial commands may be annoying.
Especially, when you have to do some experiments first, e.g. what command will work or which dependencies you need.
It can be even harder when you are working on an operating system different from the target OS.
Pushing and re-running the workflow each time is a nightmare.

This repository tries to simplify this kind of work.
With it, you can start a single job that waits for your commands.
This way, you can prepare your commands for a workflow interactively without committing, pushing, and long waiting.

## How to use it

1. Install `ZeroTier`. \
   https://www.zerotier.com/download/
1. Create your private network if you don't have it. \
   https://my.zerotier.com/
1. Connect to your private network from your machine using GUI or the following command:
   ```
   sudo zerotier-cli join <network ID>
   ```
1. Fork this repository on GitHub.
1. Clone this repository to your machine.
1. Create new ssh and ZeroTier keys:
   ```
   ./manage.sh all
   ```
1. Copy keys and ids to GitHub Actions secrets in your fork's configuration:
   * Your private network id to the `NETWORK_ID` secret.
   * The `identity.secret` file content to the `IDENTITY` secret.
     You can keep the member ID (first 10 characters) to later identify which private network member is a GitHub Actions runner.
   * The `host_key` file content to the `HOST_KEY` secret.
   * The `client_key.pub` to the `CLIENT_KEY` secret.
     * You can add multiple client keys to the secret.
     * Each key must be in a separate line.
     * To create a new client key use the following command:
       ```
       ./manage.sh client_key my_client_key2
       ```
     * Or, you can use your existing public client keys from your `~/.ssh/` directory.
1. Run the GitHub Action on your fork.
1. Runner will be ready to connect when `Your work starts here` step is running.
1. Accept new members of your private network at https://my.zerotier.com/. Newly assigned IP address of the runner will be needed later. If you don't see the address immediately, wait and refresh the page.
1. Connect with ssh:
   ```
   ssh runner@<your runner ip address> -p 9852 -i <your client_key>
   ```
1. After connecting, server will print some useful information. Read them.
1. Inside SSH session, you can run the following command to end the GitHub Action:
   ```
   exit_job
   ```
   Alternatively, you can use GitHub web page to cancel the action.
