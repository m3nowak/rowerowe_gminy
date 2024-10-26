# rowerowe_gminy

Repozytroium backendowe aplikacji Rowerowe Gminy

# Uprawnienia NATS

## WKK

```json
{
  "pub": {
    "allow": [
      "$JS.ACK.incoming-wha.wkk.>",
      "$JS.API.CONSUMER.CREATE.KV_rate-limits",
      "$JS.API.CONSUMER.INFO.KV_rate-limits.*",
      "$JS.API.CONSUMER.MSG.NEXT.incoming-wha.wkk",
      "$JS.API.DIRECT.GET.KV_rate-limits.$KV.rate-limits.>",
      "$JS.API.DIRECT.GET.KV_wkk-auth.$KV.wkk-auth.>",
      "$JS.API.STREAM.INFO.KV_rate-limits",
      "$JS.API.STREAM.INFO.KV_wkk-auth",
      "$JS.API.STREAM.MSG.GET.KV_rate-limits",
      "$JS.API.STREAM.MSG.GET.KV_wkk-auth",
      "$JS.API.STREAM.NAMES",
      "$KV.rate-limits.*"
    ]
  },
  "sub": {
    "allow": ["_inbox.wkk.>"]
  }
}
```
