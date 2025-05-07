# a2e Package

This package contains the A2e module and wraps all of the other packages to make importing modules easy. Each of the sub-packages are explained in detail in their own README files. For more information on the A2e module, keep reading.

## A2e Module

The A2e module is a high-level interface that allows the programmer to use our API to authenticate, search, and download the data they want in very few lines of code.

## Setup

First, import the module:

```python
from a2e import A2e
```

Then, create an instance of the A2e class:

```python
a2e = A2e.A2e()
```

And that's it! Setup is complete. All future methods will revolve around this `a2e` object. Alternatively, the constructor accepts two optional arguments: `cert` and `quiet`. The cert argument takes in a cert string. The quiet argument when set to `True` disables output. Useful for scripting.

### Authentication

Authentication is very simple with this module. This module supports both __basic__ and __certificate__ authentication protocols. The basic methods do not use a certificate, expire more quickly, and do not support two-factor authentication. The other methods in this module will not work without proper authentication. When an A2e instance is created, the constructor looks for any existing certificates in `~/.cert` and tries to renews it. Alternatively, a certificate can be passed into the constructor:

```python
a2e = A2e(<cert>)
```

If the certificate is valid, it will be renewed and written to the `~/.cert` file. Otherwise, it defaults to basic guest authentication. The following are the different authentication methods:

#### `a2e.setup_guest_auth()`

Sets up basic authentication for a guest user. This is identical to setting up basic authentication with the username and password `guest`.

#### `a2e.setup_basic_auth(username=None, password=None)`

Sets up basic authentication with a username and password. The arguments are optional, but the module will prompt for them if omitted.

#### `a2e.setup_cert_auth(username=None, password=None)`

Similar to the method above, but will request a certificate instead of using basic authentication. The certificate is stored in the `~./cert` file. Will prompt user for omitted arguments.

#### `a2e.setup_two_factor_auth(username=None, password=None, email=None, authcode=None)`

Similar to the method above, but uses two-factor authentication. The authcode is the 6 digit number from Google Authenticator. This is the highest authentication level available. The certificate is stored in the `~./cert` file. Will prompt user for omitted arguments.

### Searching for Files

Searching is straight-forward with this module. Simple call this method and a list of files will be returned.

#### `a2e.search(filter_arg, table='Inventory')`

Query the respective table in AWS with the given filter argument. An example filter argument is shown below:

```python
filter_arg = {
    'Dataset': 'wfip2/lidar.z01.b0',
    'date_time': {
        'between': ['20160101000000', '20160104000000']
    },
    'file_type': 'nc',
}
```

The documentation for constructing the filter argument can be found [here](https://github.com/a2edap/dap-py/blob/master/a2e/download-README.md).

### Downloading Files

There are two ways to download files using this module. The first places an order for the files, gets the download urls, and downloads the files to the provided path. The second uses the `/downloads` api method to search for the files and download them to the provided path in one step. The latter is dangerous if you don't know how many files you are about to download!

#### `a2e.download_files(files, dataset, path='/var/tmp/', force=False)`

Provided with a list of files, place an order for the files and download them. The path specifies the directory the files will download to, and the force flag determines whether files will be overriden. By default, if a file already exists, it will not be downloaded. Does not work using guest credentials because guests cannot place an order.

#### `a2e.download_search(filter_arg, path='/var/tmp/', force=False)`

Provided with a [filter argument](https://github.com/a2edap/dap-py/blob/master/a2e/download-README.md), search the Inventory table and download the files in s3. I heard a rumor through the grapevine that only files in s3 will be downloaded, so if you think some data could be someone else, use the other download method.

## Example

```python
from A2e import A2e

a2e = A2e.A2e()

dataset = "wfip2/lidar.z01.b0"

files = a2e.search({
    'Dataset': dataset,
    'date_time': {
        'between': ['20160101000000', '20160104000000']
    },
    'file_type': 'nc',
})

a2e.download_files(files, dataset, force=True)
```
