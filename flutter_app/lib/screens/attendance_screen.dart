import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/ble_service.dart';
import '../services/face_service.dart';
import '../services/crypto_service.dart';
import '../services/api_service.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

class AttendanceScreen extends StatefulWidget {
  const AttendanceScreen({Key? key}) : super(key: key);

  @override
  _AttendanceScreenState createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends State<AttendanceScreen> {
  int _currentStep = 0;
  final BleService _bleService = BleService();
  final FaceService _faceService = FaceService();
  final String SECRET_HMAC_KEY = "my_super_secret_key";
  Map<String, dynamic>? _classDetails;
  String _statusMessage = "";

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_classDetails == null) {
      _classDetails = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>?;
      if (_currentStep == 0) _startProcess();
    }
  }

  Future<void> _startProcess() async {
    setState(() { _currentStep = 0; _statusMessage = ""; });
    
    // Step 1: BLE
    bool found = await _bleService.scanForUUID(_classDetails?['esp32_uuid'] ?? '');
    if (!found) {
      setState(() { _statusMessage = "BLE Beacon not found. Are you in the classroom?"; _currentStep = -1; });
      return;
    }

    setState(() => _currentStep = 1);
    
    // Step 2: Face (Dummy placeholder for camera flow)
    await Future.delayed(const Duration(seconds: 2));
    List<double> dummyEncoding = List.generate(128, (i) => 0.1); 

    setState(() => _currentStep = 2);

    // Step 3: API
    final prefs = await SharedPreferences.getInstance();
    String? rollNo = prefs.getString('roll_no') ?? '';
    String timestamp = DateTime.now().toIso8601String();
    String hmac = CryptoService.generateHMAC(rollNo, _classDetails?['esp32_uuid'] ?? '', timestamp, SECRET_HMAC_KEY);

    try {
      await ApiService().verifyAttendance({
        'roll_no': rollNo,
        'timetable_id': _classDetails?['timetable_id'],
        'live_face_encoding': dummyEncoding,
        'scanned_ble_uuid': _classDetails?['esp32_uuid'],
        'app_timestamp': timestamp,
        'hmac_signature': hmac,
      });
      setState(() => _currentStep = 3);
    } catch (e) {
      setState(() { _statusMessage = "API Error: $e"; _currentStep = -1; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Attendance: ${_classDetails?['subject'] ?? ''}')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            ListTile(
              leading: _getStepIcon(0),
              title: const Text('Scanning for classroom beacon...'),
            ),
            ListTile(
              leading: _getStepIcon(1),
              title: const Text('Verifying your identity...'),
            ),
            ListTile(
              leading: _getStepIcon(2),
              title: const Text('Submitting attendance...'),
            ),
            if (_currentStep == 3)
              const ListTile(
                leading: Icon(Icons.check_circle, color: Colors.green, size: 36),
                title: Text('Done! Attendance marked.', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ),
            if (_currentStep == -1)
              ListTile(
                leading: const Icon(Icons.error, color: Colors.red, size: 36),
                title: Text(_statusMessage, style: const TextStyle(color: Colors.red)),
                trailing: ElevatedButton(
                  onPressed: _startProcess,
                  child: const Text('Retry'),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _getStepIcon(int stepIndex) {
    if (_currentStep > stepIndex) return const Icon(Icons.check, color: Colors.green);
    if (_currentStep == stepIndex) return const CircularProgressIndicator();
    return const Icon(Icons.radio_button_unchecked);
  }
}
