import 'dart:convert';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;

import '../models/chat_models.dart';


class AriaApi {
  AriaApi({String? baseUrl, this.apiKey})
      : baseUrl = baseUrl ??
            const String.fromEnvironment(
              'ARIA_API_URL',
              defaultValue: 'http://127.0.0.1:8000',
            );

  final String baseUrl;
  final String? apiKey;

  Map<String, String> _headers() {
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (apiKey != null && apiKey!.isNotEmpty) {
      headers['X-ARIA-Key'] = apiKey!;
    }
    return headers;
  }

  Future<String> sendChat(String prompt, {String? sessionId}) async {
    final body = <String, dynamic>{
      'prompt': prompt,
      'allow_tools': true,
    };
    if (sessionId != null && sessionId.isNotEmpty) {
      body['session_id'] = sessionId;
    }

    final response = await http.post(
      Uri.parse('$baseUrl/chat'),
      headers: _headers(),
      body: jsonEncode(body),
    );

    if (response.statusCode >= 400) {
      throw Exception('Error al hablar con ARIA: ${response.body}');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['answer'] as String;
  }

  Future<List<VoiceProfile>> listProfiles() async {
    final response = await http.get(
      Uri.parse('$baseUrl/voice/profiles'),
      headers: apiKey != null && apiKey!.isNotEmpty ? {'X-ARIA-Key': apiKey!} : null,
    );
    if (response.statusCode >= 400) {
      throw Exception('No se pudieron cargar los perfiles de voz.');
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final items = data['items'] as List<dynamic>;
    return items
        .map((item) => VoiceProfile.fromJson(Map<String, dynamic>.from(item as Map)))
        .toList();
  }

  Future<void> createVoiceProfile({
    required String name,
    required PlatformFile sample,
    String language = 'es',
    String? transcriptHint,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/voice/profiles'),
    )
      ..fields['name'] = name
      ..fields['language'] = language;

    if (apiKey != null && apiKey!.isNotEmpty) {
      request.headers['X-ARIA-Key'] = apiKey!;
    }

    if (transcriptHint != null && transcriptHint.isNotEmpty) {
      request.fields['transcript_hint'] = transcriptHint;
    }

    request.files.add(
      http.MultipartFile.fromBytes(
        'sample',
        sample.bytes ?? await File(sample.path!).readAsBytes(),
        filename: sample.name,
      ),
    );

    final response = await request.send();
    if (response.statusCode >= 400) {
      throw Exception('No se pudo crear el perfil de voz.');
    }
  }

  Future<Map<String, dynamic>> sendAudioChat({
    required PlatformFile audio,
    String? sessionId,
    String? voiceId,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/voice/chat'),
    );

    if (apiKey != null && apiKey!.isNotEmpty) {
      request.headers['X-ARIA-Key'] = apiKey!;
    }

    if (sessionId != null && sessionId.isNotEmpty) {
      request.fields['session_id'] = sessionId;
    }
    if (voiceId != null && voiceId.isNotEmpty) {
      request.fields['voice_id'] = voiceId;
    }

    request.files.add(
      http.MultipartFile.fromBytes(
        'audio',
        audio.bytes ?? await File(audio.path!).readAsBytes(),
        filename: audio.name,
      ),
    );

    final response = await request.send();
    if (response.statusCode >= 400) {
      throw Exception('No se pudo procesar el audio.');
    }

    final body = await response.stream.bytesToString();
    return jsonDecode(body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> synthesizeVoice({
    required String text,
    String? voiceId,
    String language = 'es',
  }) async {
    final body = <String, dynamic>{
      'text': text,
      'language': language,
    };
    if (voiceId != null && voiceId.isNotEmpty) {
      body['voice_id'] = voiceId;
    }

    final response = await http.post(
      Uri.parse('$baseUrl/voice/synthesize'),
      headers: _headers(),
      body: jsonEncode(body),
    );

    if (response.statusCode >= 400) {
      throw Exception('Error sintetizando voz: ${response.body}');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }
}
