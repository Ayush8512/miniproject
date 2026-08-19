import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/attendance_screen.dart';

final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  const AndroidInitializationSettings initializationSettingsAndroid = AndroidInitializationSettings('@mipmap/ic_launcher');
  const DarwinInitializationSettings initializationSettingsIOS = DarwinInitializationSettings();
  const InitializationSettings initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid, 
      iOS: initializationSettingsIOS);
      
  await flutterLocalNotificationsPlugin.initialize(initializationSettings);
  
  runApp(const SmartAttendanceApp());
}

class SmartAttendanceApp extends StatelessWidget {
  const SmartAttendanceApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Attendance SaaS',
      theme: ThemeData(
        primarySwatch: Colors.indigo,
        primaryColor: Colors.blue,
      ),
      initialRoute: '/login',
      routes: {
        '/login': (context) => const LoginScreen(),
        '/home': (context) => const HomeScreen(),
        '/attendance': (context) => const AttendanceScreen(),
      },
    );
  }
}
