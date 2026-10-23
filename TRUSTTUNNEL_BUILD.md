# TrustTunnel Android Anti-DPI (experimental)

Builds a separate debug Android APK from the official [TrustTunnelFlutterClient](https://github.com/TrustTunnel/TrustTunnelFlutterClient) tag `v1.2.0` using the local `apply_anti_dpi.py` patch. No VPN accounts or keys are committed.

Workflow: [Build TrustTunnel Anti-DPI APK](../../actions/workflows/build-android.yml). A successful run uploads an artifact named `trusttunnel-antidpi-debug-arm64`.

**Notes:** Unofficial build. Android app ID `com.adguard.trusttunnel.antidpi`, installed alongside the Play Store version; add VPN profile manually. Does not hide the server IP; anti-DPI may not help with packet loss. The upstream project may require `GPR_KEY` as a GitHub Actions repository secret with `read:packages` to restore native dependencies. Never paste keys into commits or discussions.

This repo is publicly visible, so don't put VPN configurations, credentials or logs here.
