# Examples

Run from the project root (scripts `cd` up automatically):

```bash
bash examples/generate_one.sh      # one B1 video
bash examples/batch.sh             # five A2 videos
bash examples/daily_accounts.sh    # one batch per account
```

Equivalent direct commands:
```bash
python -m app.main one --level B1
python -m app.main batch --count 5 --level A2
python -m app.main accounts
```
