import 'dart:async';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

class BleService {
  Future<bool> scanForUUID(String targetUUID, {Duration timeout = const Duration(seconds: 15)}) async {
    // Request permissions
    Map<Permission, PermissionStatus> statuses = await [
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
      Permission.location,
    ].request();

    if (statuses.values.any((status) => !status.isGranted)) {
      return false;
    }

    bool found = false;
    StreamSubscription<List<ScanResult>>? subscription;
    
    try {
      await FlutterBluePlus.startScan(timeout: timeout);
      Completer<bool> completer = Completer<bool>();
      
      subscription = FlutterBluePlus.scanResults.listen((results) {
        for (ScanResult r in results) {
          final uuids = r.advertisementData.serviceUuids.map((e) => e.toString().toLowerCase()).toList();
          if (uuids.contains(targetUUID.toLowerCase())) {
            found = true;
            FlutterBluePlus.stopScan();
            if (!completer.isCompleted) completer.complete(true);
            break;
          }
        }
      });

      found = await completer.future.timeout(timeout, onTimeout: () => false);
    } catch (e) {
      return false;
    } finally {
      subscription?.cancel();
      await FlutterBluePlus.stopScan();
    }
    return found;
  }
}
