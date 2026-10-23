#!/usr/bin/env python3
"""Patch TrustTunnelFlutterClient v1.2.0 to enable per-server Anti-DPI.

Usage: python3 apply_anti_dpi.py PATH_TO_UPSTREAM_CHECKOUT
Checks all source anchors before writing modified files.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else Path.cwd()
changes = {}

def load(path):
    p = root / path
    if not p.exists():
        raise SystemExit(f'Missing {p}: checkout upstream tag v1.2.0')
    return changes.get(path, p.read_text(encoding='utf-8'))

def replace(path, old, new, count=1):
    source = load(path)
    if source.count(old) == count:
        changes[path] = source.replace(old, new, count)
        return
    # Allow Dart formatter to vary indentation, but not code.
    old_lines = old.splitlines()
    pattern = r'(?m)' + r'\n'.join(
        r'^[ \t]*' + re.escape(line.strip()) for line in old_lines
    )
    matches = list(re.finditer(pattern, source))
    if len(matches) != count:
        raise SystemExit(f'ABORT {path}: expected {count} anchors, found {len(matches)}: {old!r}')
    first_indent = len(old_lines[0]) - len(old_lines[0].lstrip())
    new_lines = new.splitlines()
    def rewrite(match):
        first_line = match.group(0).splitlines()[0]
        indent = len(first_line) - len(first_line.lstrip())
        return '\n'.join(
            ' ' * max(0, indent + len(line) - len(line.lstrip()) - first_indent) + line.lstrip()
            for line in new_lines
        )
    changes[path] = re.sub(pattern, rewrite, source)

model = 'lib/data/model/server_data.dart'
replace(model, '  final bool selected;', '  final bool selected;\n\n  /// Extra transport measures for DPI resistance.\n  final bool antiDpi;')
replace(model, '    this.selected = false,', '    this.antiDpi = false,\n    this.selected = false,', count=2)
replace(model, '    selected,\n    certificate,', '    selected,\n    antiDpi,\n    certificate,')
replace(model, "       'selected: $selected,'", "       'selected: $selected,'\n       'antiDpi: $antiDpi,'")
replace(model, '        other.selected == selected &&', '        other.selected == selected &&\n        other.antiDpi == antiDpi &&')
replace(model, '    bool? selected,', '    bool? selected,\n    bool? antiDpi,')
replace(model, '    selected: selected ?? this.selected,', '    selected: selected ?? this.selected,\n    antiDpi: antiDpi ?? this.antiDpi,')

replace('lib/data/database/tables/servers_table.drift',
        '  ipv6_enabled BOOLEAN NOT NULL DEFAULT true,',
        '  ipv6_enabled BOOLEAN NOT NULL DEFAULT true,\n  anti_dpi BOOLEAN NOT NULL DEFAULT false,')

database = 'lib/data/database/app_database.dart'
replace(database,
        "import 'package:trusttunnel/data/database/migrations/migrations_v4.dart';",
        "import 'package:trusttunnel/data/database/migrations/migrations_v4.dart';\nimport 'package:trusttunnel/data/database/migrations/migrations_v5.dart';")
replace(database, 'int get schemaVersion => 4;', 'int get schemaVersion => 5;')
replace(database,
        "      if (from < 4) {\n        await _runMigrationStep('v4', () => const MigrationsV4().migrate(this, m));\n      }",
        "      if (from < 4) {\n        await _runMigrationStep('v4', () => const MigrationsV4().migrate(this, m));\n      }\n      if (from < 5) {\n        await _runMigrationStep('v5', () => const MigrationsV5().migrate(this, m));\n      }")
changes['lib/data/database/migrations/migrations_v5.dart'] = """import 'package:drift/drift.dart';
import 'package:trusttunnel/data/database/app_database.dart' as db;
import 'package:trusttunnel/data/database/migrations/migrations.dart';

class MigrationsV5 implements Migrations {
  const MigrationsV5();

  @override
  Future<void> migrate(GeneratedDatabase database, Migrator m) async {
    final appDatabase = database as db.AppDatabase;
    await m.addColumn(appDatabase.servers, appDatabase.servers.antiDpi);
  }
}
"""

datasource = 'lib/data/datasources/local_sources/server_datasource_impl.dart'
replace(datasource, '         ipv6Enabled: Value(request.ipv6),',
        '         ipv6Enabled: Value(request.ipv6),\n         antiDpi: Value(request.antiDpi),', count=2)
replace(datasource, '         ipv6: request.ipv6,',
        '         ipv6: request.ipv6,\n         antiDpi: request.antiDpi,')
replace(datasource, '             ipv6: e.ipv6Enabled,',
        '             ipv6: e.ipv6Enabled,\n             antiDpi: e.antiDpi,')
replace(datasource, '         ipv6: server.ipv6Enabled,',
        '         ipv6: server.ipv6Enabled,\n         antiDpi: server.antiDpi,')
replace(datasource, '       ipv6: configuration.endpoint.hasIpv6,',
        '       ipv6: configuration.endpoint.hasIpv6,\n       antiDpi: configuration.endpoint.antiDpi,')

vpn = 'lib/data/datasources/native_sources/vpn_datasource_impl.dart'
replace(vpn, '     final endPoint = Endpoint(\n       name: server.name,',
        '     final endPoint = Endpoint(\n       antiDpi: server.antiDpi,\n       name: server.name,', count=2)

controller = 'lib/feature/server/server_details/controller/servers_details_controller.dart'
replace(controller, '     bool? enableIpv6,', '     bool? enableIpv6,\n     bool? antiDpi,')
replace(controller, '             ipv6: enableIpv6 ?? state.data.ipv6,',
        '             ipv6: enableIpv6 ?? state.data.ipv6,\n             antiDpi: antiDpi ?? state.data.antiDpi,')

scope = 'lib/feature/server/server_details/widgets/scope/server_details_scope_controller.dart'
replace(scope, '       bool? enableIpv6,', '       bool? enableIpv6,\n       bool? antiDpi,')

form = 'lib/feature/server/server_details/widgets/server_details_form.dart'
replace(form, '               CustomDropdownMenu<RoutingProfile>.expanded(',
        "               CheckboxListTile(\n"
        "                 value: _formData.antiDpi,\n"
        "                 title: const Text('Anti-DPI'),\n"
        "                 subtitle: const Text('Extra DPI resistance for this endpoint'),\n"
        "                 contentPadding: const EdgeInsets.all(4),\n"
        "                 onChanged: (value) => _onDataChanged(context, antiDpi: value),\n"
        "               ),\n"
        "               CustomDropdownMenu<RoutingProfile>.expanded(")
replace(form, '     bool? enableIpv6,', '     bool? enableIpv6,\n     bool? antiDpi,')
replace(form, '         enableIpv6: enableIpv6,',
        '         enableIpv6: enableIpv6,\n         antiDpi: antiDpi,')

gradle = 'android/app/build.gradle'
replace(gradle, 'applicationId = "com.adguard.trusttunnel"',
        'applicationId = "com.adguard.trusttunnel.antidpi"')
replace(gradle, 'storeFile = rootProject.file(getSigningProp("signingConfigKeyStorePath"))',
        'storeFile = rootProject.file(getSigningProp("signingConfigKeyStorePath") ?: "debug.keystore")')

changes['test/anti_dpi_feature_test.dart'] = """import 'package:flutter_test/flutter_test.dart';
import 'package:trusttunnel/data/model/server_data.dart';
import 'package:vpn_plugin/domain/configuration_codec.dart';
import 'package:vpn_plugin/models/configuration.dart';
import 'package:vpn_plugin/models/endpoint.dart';
import 'package:vpn_plugin/models/upstream_protocol.dart';
import 'package:vpn_plugin/models/vpn_mode.dart';
import 'package:vpn_plugin/models/tun.dart';
import 'package:vpn_plugin/models/socks.dart';

void main() {
  test('Anti-DPI defaults false and survives copyWith', () {
    const server = ServerData.empty();
    expect(server.antiDpi, isFalse);
    expect(server.copyWith(antiDpi: true).antiDpi, isTrue);
  });

  test('Configuration serializes anti_dpi to the VPN core', () {
    final endpoint = Endpoint(
      name: 'test',
      hostName: 'vpn.endpoint',
      username: 'test',
      password: 'dummy',
      upStreamProtocol: UpStreamProtocol.http2,
      hasIpv6: false,
      antiDpi: true,
      addresses: const ['127.0.0.1:443'],
    );
    final config = Configuration(
      endpoint: endpoint,
      vpnMode: VpnMode.general,
      tun: const Tun(),
      socks: const Socks(),
    );
    expect(const ConfigurationEncoder().convert(config), contains('anti_dpi = true'));
  });
}
"""

# Every anchor is checked before any file is written.
for path in changes:
    if not (root / path).is_file() and path not in (
        'lib/data/database/migrations/migrations_v5.dart',
        'test/anti_dpi_feature_test.dart',
    ):
        raise SystemExit(f'ABORT unexpected missing source file: {path}')

for path, data in changes.items():
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding='utf-8')
    print('patched', path)

print(f'Patched {len(changes)} files; generate Drift sources before compiling.')
