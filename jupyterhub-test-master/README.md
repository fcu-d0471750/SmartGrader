# SmartGrader
**SmartGrader** uses JupyterHub as the main development platform and it is extended based on the system architecture of the nbgrader module.

# Installation
SmartGrade **can only set up in Linux.**

## Step 1
You need to clone this project. Installation path can decided by yourslef.  
<pre><code>git clone https://github.com/CSFeng0826/jupyterhub-test</code></pre>  
In SmartGrader project has three folders, the folder's details are as follows:
* <code>build</code> : The Dockerfile which build ***JupyterHub*** with ***nbgrader*** is store in this folder.
* <code>config_folder</code> : In this folder contains the basic config.
* <code>server</code> : In this folder contains flask api which is used to collect log and provide student's information.

## Step 2
Modify <code>.env</code> and <code>jupyterhub_config.py</code>.  
You can check <code>env.example</code> and <code>example.jupyterhub_config.py</code>

## Step 3
Build up SmartGrader. Please insure you are at root path.  
<pre><code>sudo docker-compose build</code></pre>
<pre><code>sudo docker-compose up -d</code></pre>  

## Step 4
Add user  
1. Update user passwd  
<pre><code>sudo docker exec -it jupyterhub passwd <user></pre></code>  
2. Adduser  
<pre><code>sudo docker exec -it jupyterhub useradd --create-home <user></pre></code>  
<pre><code>sudo docker exec -it jupyterhub passwd <user></pre></code>  
