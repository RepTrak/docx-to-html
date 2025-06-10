# Docker Installation Guide for CentOS Stream 10

Docker must be installed in order to run LibreOffice as used in scripts/full_pipeline.py or scripts/libre_office_convert.sh. Here is the installation process for Docker on **CentOS Stream 10**.

Note: Docker should be installed on the server's root, and the user running LibreOffice must be included in the server's Docker group.

---

### Step 1: Update System Packages

```bash
sudo dnf update -y
```

### Step 2: Install Required Dependencies

```bash
sudo dnf install -y yum-utils device-mapper-persistent-data lvm2
```

### Step 3: Add Docker Repository

```bash
sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
```

### Step 4: Install Docker Engine

```bash
sudo dnf install -y docker-ce docker-ce-cli containerd.io
```

### Step 5: Start Docker Service

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### Adding a user to the Docker group

If a "permission denied" error is encountered, this is likely due to the user not being in the server's Docker group. To add the user, run:

```bash
sudo usermod -aG docker user_name
```

Then, log out and fully log back in to apply group changes. Group membership can be verified by running

```bash
groups
```
