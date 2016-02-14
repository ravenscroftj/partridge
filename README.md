Partridge
=================

Partridge is an automated scientific literature retrieval and recommendation suite. 
It was my dissertation project during 2012-2013 at Aberystwyth University, Wales.

Partridge provides a full pipeline for conversion, annotation and
classification of scientific papers. It uses some external tools but also a
fair amount of novel behaviour during this process. A web interface is also
provided so that papers can be indexed and searched. The long term goal is to
provide content-based recommendations for users of the system.

PDF Conversion
----------------
Partridge uses [PDFX](http://pdfx.cs.man.ac.uk/), a tool provided by Alexander
Constantin at the University of Manchester, for extracting
[JATS](http://jats.nlm.nih.gov/archiving/) compatible XML for processing and
annotation. 

Scientific Concept Annotation
------------------------------
Partridge makes use of [SAPIENTA](http://sapientaproject.com/), a machine
learning classifier written by Maria Liakata et al., to annotate the scientific
concepts within papers sentence-by-sentence. This allows a deeper understanding
of the structure of the papers and is also used for paper type classification.

Paper Type Classification
---------------------------
Paper type classification is novel behaviour within Partridge. A Random Forest
classifier has been trained to recognise types of paper (Research Article,
Review, Case Study etc.) based on a paper's scientific concept annotations.


Installing Partridge
=======================

If you want to use Partridge to find a paper, you don't need to download and install
this package. There is an instance running at http://farnsworth.papro.org.uk/

The following instructions are for those interested in setting up their own instance of Partridge
or for modifying my code.

System Requirements
-------------------------
  * Partridge requires Python 2.7.3 and an SQL database backend supported by SQLAlchemy. 
  * Partridge *should* be cross platform, but hasn't been fully tested on MacOSX or Windows.
  * SQLite3 comes with Python by default, but is not recommended for large scale Partridge installations.
  * Partridge was developed on an Arch Linux desktop computer with Python 2.7.3 and MySQL backend server.
  * http://farnsworth.papro.org.uk/ is a CentOS 6 box with Python 2.7.3 and MySQL backend.

Installation
-------------------------

### VirtualEnv ###

It is recommended that you install Partridge into a [VirtualEnv](http://www.virtualenv.org/en/latest/) 
environment on your system rather than adding it to your system-wide Python installation. If you aren't 
familiar with VirtualEnv, it is essentially a way of sandboxing Partridge's run environment from your 
system-wide python installation, preventing problems with module dependencies and security issues.

### Dependencies ###

#### SAPIENTA ####

SAPIENTA is currently also a dependency of Partridge. You can get it from [here](https://bitbucket.org/partridge/sapienta/).

You need to make sure you install SAPIENTA and Partridge in the same virtualenv.

#### Library/System dependencies ####

Partridge was written and runs on Ubuntu. It is suggested that you install it on a unix/linux system that is similar to Ubuntu. It will run happily on OS/X but some of the commands here will not work.

Partridge requires the *libmysqlclient-dev*  package installed so that it can run with a MySQL database (or you can use SQLite or whatever other database you want). 

Partridge was written in and runs in *python2* so it probably won't work in Python 3 at the moment.

#### Python dependencies ####

Partridge has several dependencies that it requires to run successfully. These are:

  * [Flask](http://flask.pocoo.org/) 
  * [Flask-SQLAlchemy](http://pythonhosted.org/Flask-SQLAlchemy/)
  * [pycurl](http://pycurl.sourceforge.net/)
  * [NLTK](http://nltk.org/)
  * [python-progressbar](https://pypi.python.org/pypi/progressbar/2.2)
  * [pyinotify](https://github.com/seb-m/pyinotify)
  * [Alembic](https://bitbucket.org/zzzeek/alembic)
  * [Orange](http://orange.biolab.si/)

**Please note: You will need to make sure that the relevant database backend is installed for SQLAlchemy 
to be able to communicate with your database. This is not done automatically. Python was built and tested 
with MySQL. However, there is a full list of supported 
[SQL dialects and respective libraries here](http://docs.sqlalchemy.org/en/rel_0_8/dialects/).**

Partridge has a distutils boostrap script that will try and install these libraries (and their respective 
dependencies) when you build the system. However, it will compile them from source which is a slow process. 
If you have the option to install binary packages for Orange and NLTK, it is worth doing this beforehand.

### Typical Installation Workflow ###

First, check out the repository from GIT.

    $ git clone https://github.com/ravenscroftj/partridge.git
    Cloning into 'partridge'...

Set up the virtual environment and run the source command to start using the new environment.

    $ cd partridge
    $ virtualenv env
    New python executable in env/bin/python2
    Also creating executable in env/bin/python
    Installing setuptools............done.
    Installing pip...............done.
    $ source env/bin/activate

A little (env) should appear indicating that you have entered the virtual environment. Now install your database driver
using pip. For a Partridge installation that will use [MySQL](http://www.mysql.com/), run the following command. If you intend to use
a different RDBMS, you should replace `mysql-python` with the relevant library listed [here](http://docs.sqlalchemy.org/en/rel_0_8/dialects/).

    (env) $ pip install mysql-python
    Downloading/unpacking mysql-python
    ...
    ...
    
Next you will need to clone and install SAPIENTA (inside the partridge directory).

    (env) $ git clone git@bitbucket.org:partridge/sapienta.git
    Cloning into 'sapienta'
    ...
    ...

You should follow the guide to install SAPIENTA and ensure that you use the same python virtualenv for both systems.

Finally, you can build the Partridge subsystem and dependencies with the following command.

    (env) $ python setup.py install
    running install
    running bdist_egg
    running egg_info
    ...
    ...

#### Installing paper types model.

Create a directory inside your partridge project dir called "models" and download the pre-built decision tree model into it from [here](https://www.dropbox.com/s/lrgx6y7j9m82w0o/paper_types.model?dl=0).


### Configuration

Partridge uses a simple configuration file called `partridge.cfg`. The program will look for the existence of such a file at runtime
in the following locations:

  1. If you specify `-c filename.cfg` when running Partridge, it will try to use the provided filename first.
  2. If `-c` is not set, it will check for the existence of a `PARTRIDGE_CONF` variable set by your terminal environment
  3. If no environment variable is set, it will look in the current working directory for a `partridge.cfg` file.
  4. If no file could be found in the current working directory, it will try looking in `/home/yourname/.config/` for a config file.
  5. If no file was found in your home dir, the system will try /etc/partridge.cfg for a systemwide configuration file.

Setting up your configuration file is simple, rename the provided sample (`partridge.cfg.sample`) and place it in the appropriate directory. 
The below table illustrates each option and what it does

<table>
	<tr>
		<th><b>Variable Name</b></th>
		<th><b>Description</b></th>
	</tr>
	<tr>
		<td>`DEBUG`</td>
		<td>If set to True, puts Flask and Partridge into debug mode and maximises log verbosity levels. Legal values: True, False
		</td>
	</tr>
	<tr>
		<td>`SQLALCHEMY_DATABASE_URI`</td>
		<td>This is a connection string passed straight to SQLAlchemy in order to connect to your backend. SQLAlchemy provide
		     documentation on how to form a connection string for your preferred database backend 
                     [here](http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html#database-urls). Example connection strings for SQLite and
		     MySQL are provided in the sample config file.
		</td>
	</tr>
	<tr>
		<td>`PAPER_UPLOAD_DIR`</td>
		<td>This is the directory that papers are uploaded to when they are queued to be processed. This is usually a subdirectory
		of the Partridge environment that you installed using the instructions above.</td>
	</tr>
	<tr>
		<td>`PAPER_PROC_DIR`</td>
		<td>Similar to the above, this is the path to the directory where processed files are stored. Again, usually within the 
		Partridge environment.</td>
	</tr>
	<tr>
		<td>`MODELS_DIR`</td>
		<td>This is the path of the models directory which is where Partridge stores its machine learning classifier models. This
		is the absolute path to the `models` directory just inside Partridge's top level directory.</td>
	</tr>
	<tr>
		<td>`SERVER_NAME`</td>
		<td>(Optional) This variable is set if your server has multiple domain/host names (because it is a virtual private server or 
		hosts a number of separate websites. This is just a hostname value such as "farnsworth.papro.org.uk" that Partridge should 
		listen for requests on.</td>
	</tr>
	<tr>
		<td>`NOTIFICATION_SMTP_ADDRESS`</td>
		<td>(Optional) If you wish to be notified every time a paper fails (this is *as well as* letting the paper submitter know that it 			failed), then enter an email address to send these notifications to here.</td>
	</tr>
	<tr>
		<td>`NOTIFICATION_SMTP_SERVER`</td>
		<td>(Optional) If you wish to send out email notifications, this is the address of the SMTP server to send notifications from.</td>
	</tr>
	<tr>
		<td>`NOTIFICATION_SMTP_USER`</td>
		<td>(Optional) If your SMTP server requires authentication, this is the username to authenticate with.</td>
	</tr>
	<tr>
		<td>`NOTIFICATION_SMTP_PASWD`</td>
		<td>(Optional) If your SMTP server requires authentication, this is the password to authenticate with.</td>
	</tr>
	<tr>
		<td>`NOTIFICATION_SMTP_FROM`</td>
		<td>(Optional) This is the email address that notifications claim to have been sent from. It can be distinct
		from your `NOTIFICATION_SMTP_USER` value.</td>
	</tr>
</table>

### Installing the database ###
Once you have set up your relational database backend, configured the SQLAlchemy connection string as detailed above 
and created an empty database for Partridge's data to go into, you can initialise the schema and start the server 
with the following command:

    (env) $ partridged --initdb


Running Partridge
---------------------

Running Partridge as a standalone server is very simple provided you have successfully installed and configured
the system as detailed in the previous sections of this document, you can run Partridge using

    (env) $ partridged

There are several commands that can be specified at runtime through the use of commandline arguments. Use `partridged --help` 
for more information.

Using Partridge with WSGI
--------------------------

### Configuring WSGI ###

If you want to run Partridge in a WSGI environment, you will need to [configure WSGI](http://wsgi.readthedocs.org/en/latest/) 
to use the `partridge.wsgi` file as an entrypoint. You'll want to update the paths in `partridge.wsgi` to point to the right
folders and directories on your installation path.

### Paper Daemon ###

There was no easy way for me to make the paper preprocessor daemon run as part of the WSGI service, so you still need to run 
the paper daemon as a separate process. Running `partridged --paperdaemon` will start the Partridge standalone server without the
web frontend, and provided that it shares the same `partridge.cfg` file as the WSGI setup, will handle papers uploaded through the 
WSGI interface automatically.

