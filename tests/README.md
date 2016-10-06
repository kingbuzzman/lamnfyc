`cd tests`
`pip install -r requirements.txt`
`PYTHONPATH=..:$PYTHONPATH ./runtests.py`
`flake8 --config=.flakerc ../lamnfyc`

If you want to be REALLY safe:

`virtualenv /tmp/test-lamnfyc`
`/tmp/test-lamnfyc/bin/pip install -r requirements.txt`
`PYTHONPATH=..:$PYTHONPATH /tmp/test-lamnfyc/bin/coverage run runtests.py`
`/tmp/test-lamnfyc/bin/coverage report -m`

To test PEP8-ness

`/tmp/test-lamnfyc/bin/flake8 --config=.flakerc ../lamnfyc`

And when you're done testing:

`rm -rf /tmp/test-lamnfyc`
