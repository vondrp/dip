# dip

# Návod pro instalaci Klee - vycházející z: https://klee-se.org/build/build-llvm13/ 
V tomto návodu je popsána instalace nástroje Klee pro konkolické testování, který je součástí tohoto projektu. Tento postup je zaměřen výhradně na testování C kódu a knihoven, přičemž využívá STP solver, knihovnu uClibc (pro testování C knihoven) a Googletest pro unit testy.

Tento postup byl úspěšně proveden na WSL s Ubuntu 22.04.

1. Závislosti: 
Nejprve je nutné nainstalovat potřebné balíčky:

sudo apt update && sudo apt install -y build-essential git cmake llvm-13 clang-13 llvm-13-dev llvm-13-tools libboost-all-dev libgoogle-perftools-dev zlib1g-dev

2. Instalace constraint solveru (vybrán STP)
sudo apt-get install cmake bison flex libboost-all-dev python3 perl zlib1g-dev minisat

git clone https://github.com/stp/stp.git
cd stp
git checkout tags/2.3.3
mkdir build
cd build
cmake ..
make
sudo make install

Dále nastavíme neomezený limit pro zásobník:

ulimit -s unlimited

3. (Volitelné) Kompilace uClibc a modelu POSIX prostředí (nepodporováno na macOS)
Pokud potřebujete spustit reálné programy, budete potřebovat POSIX runtime a uClibc:

git clone https://github.com/klee/klee-uclibc.git
$ cd klee-uclibc
./configure --make-llvm-lib --with-cc=clang-13 --with-llvm-config=llvm-config-13

$ make -j2
$ cd ..

4. Instalace Googletest (pro unit testy)
Pro podporu unit testů je nutné stáhnout a nainstalovat Googletest:

curl -OL https://github.com/google/googletest/archive/release-1.11.0.zip
unzip release-1.11.0.zip

5. Dodatečné nástroje
Nainstalujte potřebné knihovny a nástroje:

sudo apt-get install libsqlite3-dev
pip install lit
export PATH=$PATH:/home/vondrp/.local/bin   # Nezapomeňte na správnou cestu k lit

6. Instalace Klee
Stáhněte a postavte Klee z repozitáře:

git clone https://github.com/klee/klee.git
cd klee
mkdir build
cd build

cmake -DENABLE_SOLVER_STP=ON -DENABLE_POSIX_RUNTIME=ON -DKLEE_UCLIBC_PATH=../../klee-uclibc -DENABLE_UNIT_TESTS=ON -DGTEST_SRC_DIR=../../googletest-release-1.11.0 ..
make

Tento příkaz předpokládá následující strukturu adresářů:
root
|-- klee -> build
|-- klee-uclibc
|-- googletest-release-1.11.0

7. Přidání Klee do cesty
Pro správnou funkci Klee je potřeba přidat jeho cesty do prostředí. Otevřete soubor ~/.bashrc:
nano ~/.bashrc

Na konec souboru přidejte cesty k binárním souborům a include složkám:

export PATH=$PATH:/home/vondrp/klee/build/bin
export C_INCLUDE_PATH=/home/vondrp/klee/klee/include:$C_INCLUDE_PATH

Pokud se cesty neaktualizují správně, je možné upravit konstanty v souboru config.py

## Instalace dalších věcí:
gdb: gdb --version
sudo apt install gdb

sudo apt install fzf


# Instalace rozšíření visual studio code
Instalace Node.js a npm 
sudo apt install nodejs npm

ověření: 
node -v
npm -v

(může být staršý verze - např. ubuntu 22.04 nainstalovalo verzi node v12 (nedostačující))
- takhel se uíská nová
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.4/install.sh | bash
source ~/.bashrc
nvm install --lts
nvm use --lts

Nejprve si nainstaluj Yeoman a generator pro VS Code rozšíření:
npm install -g yo generator-code

(Tento balíček ti pomůže vygenerovat základní strukturu rozšíření.)


npm install --save-dev sinon @types/sinon


sudo apt-get install libnss3

sudo apt-get install libasound2
