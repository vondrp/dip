# dip

# Návod pro instalaci Klee

Tento návod popisuje postup instalace nástroje **Klee** pro konkolické testování C kódu a knihoven. Klee využívá **STP solver**, knihovnu **uClibc** pro testování C knihoven a **GoogleTest** pro unit testy. Návod byl úspěšně proveden na systému WSL s distribucí Ubuntu 22.04.

## Krok 1: Instalace závislostí

Nejprve je nutné nainstalovat potřebné balíčky a nástroje pro kompilaci a běh Klee.

1. **Aktualizujte repozitáře a nainstalujte základní balíčky:**

    ```bash
    sudo apt update && sudo apt install -y build-essential git cmake llvm-13 clang-13 llvm-13-dev llvm-13-tools \
      libboost-all-dev libgoogle-perftools-dev zlib1g-dev
    ```

2. **Instalace STP (Constraint Solver)**

    STP je vybrán jako solver pro Klee. Pro jeho instalaci postupujte následovně:

    ```bash
    sudo apt-get install cmake bison flex libboost-all-dev python3 perl zlib1g-dev minisat
    ```

    Poté stáhněte a nainstalujte STP:

    ```bash
    git clone https://github.com/stp/stp.git
    cd stp
    git checkout tags/2.3.3
    mkdir build
    cd build
    cmake ..
    make
    sudo make install
    ```

3. **Nastavení neomezeného limitu pro zásobník:**

    Aby bylo možné provádět hluboké rekurze, je třeba nastavit neomezený limit pro zásobník:

    ```bash
    ulimit -s unlimited
    ```

## Krok 2: (Volitelné) Kompilace uClibc a POSIX modelu

Pokud potřebujete spustit reálné programy a používat POSIX runtime, budete potřebovat **uClibc**. Tento krok není podporován na macOS.

1. Stáhněte a zkompilujte **uClibc**:

    ```bash
    git clone https://github.com/klee/klee-uclibc.git
    cd klee-uclibc
    ./configure --make-llvm-lib --with-cc=clang-13 --with-llvm-config=llvm-config-13
    make -j2
    cd ..
    ```

## Krok 3: Instalace GoogleTest

Pro podporu **unit testů** je nutné nainstalovat **GoogleTest**. Stáhněte a nainstalujte:

1. Stáhněte si verzi 1.11.0 GoogleTest:

    ```bash
    curl -OL https://github.com/google/googletest/archive/release-1.11.0.zip
    unzip release-1.11.0.zip
    ```

## Krok 4: Instalace dodatečných nástrojů

1. **Nainstalujte potřebné knihovny:**

    ```bash
    sudo apt-get install libsqlite3-dev
    ```

2. **Nainstalujte Python nástroj `lit` pro spuštění testů:**

    ```bash
    pip install lit
    ```

3. **Přidejte `lit` do PATH, pokud jej používáte:**

    ```bash
    export PATH=$PATH:/home/vondrp/.local/bin   # Nezapomeňte upravit cestu k lit
    ```

## Krok 5: Instalace Klee

Nyní stáhněte a zkompilujte **Klee**:

1. **Stáhněte Klee z repozitáře:**

    ```bash
    git clone https://github.com/klee/klee.git
    cd klee
    mkdir build
    cd build
    ```

2. **Spusťte kompilaci Klee s požadovanými možnostmi:**

    ```bash
    cmake -DENABLE_SOLVER_STP=ON -DENABLE_POSIX_RUNTIME=ON -DKLEE_UCLIBC_PATH=../../klee-uclibc -DENABLE_UNIT_TESTS=ON -DGTEST_SRC_DIR=../../googletest-release-1.11.0 ..
    make
    ```

Tento příkaz předpokládá následující strukturu adresářů:
```
    |-- klee -> build
    |-- klee-uclibc
    |-- googletest-release-1.11.0
```

Pokud je vše nastaveno správně, Klee by měl být zkompilován bez chyb.

## Krok 6: Přidání Klee do cesty (PATH)

Pro pohodlné používání Klee je nutné přidat jeho binární soubory a include složky do proměnné PATH.

1. **Otevřete soubor `~/.bashrc`:**

    ```bash
    nano ~/.bashrc
    ```

2. **Na konec souboru přidejte následující řádky:**

    ```bash
    export PATH=$PATH:/home/vondrp/klee/build/bin
    export C_INCLUDE_PATH=/home/vondrp/klee/klee/include:$C_INCLUDE_PATH
    ```

3. **Uložte soubor a zavřete editor (Ctrl+X, pak Y pro uložení a Enter).**

4. **Aktivujte změny:**

    ```bash
    source ~/.bashrc
    ```

Po těchto krocích by měly být příkazy Klee dostupné z příkazového řádku. A funkční v rámci nástroje.

# Instalace QEMU (9.2.3)

Tento návod popisuje postup instalace QEMU verze 9.2.3 na systém Ubuntu 22.04 (WSL)

## Krok 1: Stažení a rozbalení QEMU

1. Stáhněte si zdrojové kódy QEMU:
    ```bash
    wget https://download.qemu.org/qemu-9.2.3.tar.xz
    ```
2. Rozbalte archiv:
    ```bash
    tar xvJf qemu-9.2.3.tar.xz
    ```
3. Přejděte do adresáře s rozbaleným QEMU:
    ```bash
    cd qemu-9.2.3
    ```

## Krok 2: Instalace závislostí

1. Aktualizujte seznam balíčků a nainstalujte potřebné závislosti:
    ```bash
    sudo apt update
    sudo apt install -y build-essential ninja-build python3-pip \
      libglib2.0-dev libfdt-dev libpixman-1.0-dev zlib1g-dev \
      libcap-ng-dev libgmp-dev libssl-dev libgtk-3-dev \
      meson pkg-config
    ```

2. Nainstalujte Python závislosti:
    ```bash
    python3 -m pip install --user tomli
    pip3 install --user sphinx sphinx_rtd_theme
    ```

3. Doplňte balíčky pro sestavení QEMU:
    ```bash
    sudo apt-get install -y libglib2.0-dev libpixman-1-dev libfdt-dev libaio-dev zlib1g-dev libssl-dev
    ```

4. Pokud používáte WSL (Windows Subsystem for Linux), nainstalujte hlavičky pro aktuální jádro:
    ```bash
    sudo apt-get install linux-headers-$(uname -r)
    ```

## Krok 3: Konfigurace a kompilace

1. Spusťte konfiguraci s požadovanými možnostmi:
    ```bash
    ./configure --prefix=/usr/local --target-list=arm-softmmu,arm-linux-user
    ```

2. Po úspěšné konfiguraci spusťte kompilaci:
    ```bash
    make -j$(nproc)
    ```

## Krok 4: Ověření instalace

1. Ověřte verzi QEMU pro ARM emulátory:

    ```bash
    /home/vondrp/programs/qemu/qemu-9.2.3/build/qemu-arm --version
    ```

2. Ověřte verzi QEMU pro ARM systém:

    ```bash
    /home/vondrp/programs/qemu/qemu-9.2.3/build/qemu-system-arm --version
    ```

Pokud tyto příkazy vrátí verzi QEMU (např. `qemu-arm version 9.2.3`), znamená to, že instalace byla úspěšná.

## Krok 5: Přidání QEMU do cesty (PATH)

Pokud chcete spustit QEMU příkazy bez zadávání celé cesty, přidejte adresář s QEMU do proměnné PATH.

1. Otevřete soubor `~/.bashrc`:
    ```bash
    nano ~/.bashrc
    ```

2. Na konec souboru přidejte následující řádek:
    ```bash
    export PATH=$PATH:/home/vondrp/programs/qemu/qemu-9.2.3/build
    ```

3. Uložte změny a zavřete editor (stiskněte `Ctrl+X`, pak `Y` pro uložení a `Enter`).

4. Aktivujte změny:
    ```bash
    source ~/.bashrc
    ```

Po přidání do cesty by měly být příkazy jako `qemu --version` nebo `qemu-system-arm --version` dostupné přímo z terminálu.

---

Tento návod vám pomůže snadno nainstalovat QEMU na vaši distribuci Ubuntu a zajistit jeho správné nastavení pro emulaci ARM systémů.


---

# Instalace dalších nástrojů

1. **Instalace GDB**

    GDB je debugger pro ladění programů:

    ```bash
    sudo apt install gdb
    gdb --version
    ```

2. **Instalace FZF (Fuzzy Finder)**

    FZF je nástroj pro fuzzy hledání souborů a dalších dat:

    ```bash
    sudo apt install fzf
    ```

---

3. **Instalace GCC pro ARM linux**

sudo apt install gcc-arm-linux-gnueabihf

4 **Instalace GDB multiarch**

sudo apt install gdb-multiarch

sudo add-apt-repository ppa:ubuntu-toolchain-r/test



# Instalace rozšíření pro Visual Studio Code

1. **Instalace Node.js a npm**

    ```bash
    sudo apt install nodejs npm
    ```

    Ověření:

    ```bash
    node -v
    npm -v
    ```

    Pokud máte starší verzi Node.js, použijte nvm pro instalaci nové verze:

    ```bash
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.4/install.sh | bash
    source ~/.bashrc
    nvm install --lts
    nvm use --lts
    ```

2. **Instalace Yeoman a generatoru pro VS Code rozšíření**

    ```bash
    npm install -g yo generator-code
    npm install --save-dev sinon @types/sinon
    sudo apt-get install libnss3
    sudo apt-get install libasound2
    ```

Tímto způsobem máte připravené všechny potřebné nástroje pro vývoj a testování.


# Nainstalovat když se chce zkompilovat clang (klee) pro platformu arm
sudo apt-get install gcc-arm-linux-gnueabi
