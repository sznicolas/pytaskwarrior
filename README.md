# pytaskwarrior
Python module wrapping Taskwarrior

Still in development, tested with task version 2.6.2 (deb)

## Howto
For now:

- `docker build -t mytaskwarrior .`
- `drit -v $PWD:/tw mytaskwarrior bash`
- `python test_exec.py`
- `cd .. && pytest`
- `cd - && python # import taskwarrior`


[Initial](https://github.com/sznicolas/pytaskwarrior/commit/f75a4bd0a66569f9e25a9ae563488129058e393b#diff-93f277324bed04c85a561677dccc3beb1afb2148c17c54aaa54393f9ecdb04cb) onboarding code by Grok.
