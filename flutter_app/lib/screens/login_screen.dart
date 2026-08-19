import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:device_info_plus/device_info_plus.dart';
import '../services/api_service.dart';
import 'dart:io';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _rollNoController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  Future<void> _login() async {
    setState(() => _isLoading = true);
    try {
      DeviceInfoPlugin deviceInfo = DeviceInfoPlugin();
      String deviceId = 'unknown';
      if (Platform.isAndroid) {
        AndroidDeviceInfo androidInfo = await deviceInfo.androidInfo;
        deviceId = androidInfo.id;
      } else if (Platform.isIOS) {
        IosDeviceInfo iosInfo = await deviceInfo.iosInfo;
        deviceId = iosInfo.identifierForVendor ?? 'unknown';
      }

      await ApiService().login(
        _rollNoController.text,
        _passwordController.text,
        deviceId,
      );

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('roll_no', _rollNoController.text);

      if (mounted) Navigator.pushReplacementNamed(context, '/home');
    } catch (e) {
      if (e.toString().contains('403')) {
        _showDialog('Device binding mismatch. Please contact admin to reset your device.');
      } else {
        _showDialog('Login failed. Please check your credentials.');
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showDialog(String message) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Error'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('OK'),
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Smart Attendance - Login')),
      body: Center(
        child: SingleChildScrollView(
          child: Card(
            margin: const EdgeInsets.all(24),
            elevation: 4,
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.school, size: 64, color: Colors.indigo),
                  const SizedBox(height: 24),
                  TextField(
                    controller: _rollNoController,
                    decoration: const InputDecoration(labelText: 'Roll No', border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _passwordController,
                    decoration: const InputDecoration(labelText: 'Password', border: OutlineInputBorder()),
                    obscureText: true,
                  ),
                  const SizedBox(height: 24),
                  _isLoading
                      ? const CircularProgressIndicator()
                      : ElevatedButton(
                          onPressed: _login,
                          style: ElevatedButton.styleFrom(
                            minimumSize: const Size.infinity,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                          child: const Text('LOGIN'),
                        ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
