from setuptools import setup

setup(
    name="InfinityCoaster",
    options={
        'build_apps': {
            'gui_apps': {
                "InfinityCoaster": "tracks.py"
            },
            'build_base': "../infinity_build",
            'plugins': [
                'pandagl',
                "p3openal_audio",
            ],
            "include_patterns": [
                "*.png",
                "dna.txt",
                "models/*"
            ],
        }
    }
)
