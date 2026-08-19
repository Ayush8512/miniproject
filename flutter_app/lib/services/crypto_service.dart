import 'dart:convert';
import 'package:crypto/crypto.dart';

class CryptoService {
  static String generateHMAC(String rollNo, String bleUUID, String timestamp, String secretKey) {
    String message = '$rollNo:$bleUUID:$timestamp';
    List<int> secretKeyBytes = utf8.encode(secretKey);
    List<int> messageBytes = utf8.encode(message);
    
    Hmac hmac = Hmac(sha256, secretKeyBytes);
    Digest digest = hmac.convert(messageBytes);
    
    return digest.toString();
  }
}
