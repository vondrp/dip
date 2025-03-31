from setuptools import setup, find_packages

setup(
    name="profiler_tool",  # Název balíčku
    version="0.1",  # Verze balíčku
    packages=find_packages(),  # Automaticky najde všechny balíčky ve struktuře
    install_requires=[  # Seznam závislostí (pokud nějaké máš)
        "argparse",  # Pokud nemáš nainstalovaný argparse (ve starších verzích Pythonu může být potřeba)
    ],
    entry_points={  # Nastavení entry pointu pro spuštění
        "console_scripts": [
            "profiler-tool=core.cli:main",  # Spustí funkci `main` z `core.cli` modulu
        ],
    },
    # Zde můžeš přidat i další metadata, např. autor, popis, licence apod.
    author="Petr Vondrovic",
    author_email="vondrovic@centrum.cz",
    description="CLI nástroj pro analýzu binárek",
    long_description=open('README.md').read(),  # Načítání popisu z README souboru
    long_description_content_type="text/markdown",
    classifiers=[  # Důležité pro správnou kategorizaci balíčku
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # Minimální verze Pythonu
)
