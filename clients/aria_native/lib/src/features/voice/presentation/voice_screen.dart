import 'dart:math';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../core/models/chat_models.dart';
import '../../../core/services/aria_api.dart';


class VoiceScreen extends StatefulWidget {
  const VoiceScreen({super.key});

  @override
  State<VoiceScreen> createState() => _VoiceScreenState();
}


class _VoiceScreenState extends State<VoiceScreen> {
  static const String _sessionIdKey = 'aria_session_id';

  final _api = AriaApi();
  final _nameController = TextEditingController();
  final _hintController = TextEditingController();

  List<VoiceProfile> _profiles = [];
  String? _selectedVoiceId;
  String? _lastTranscript;
  String? _lastAnswer;
  bool _isBusy = false;
  String? _sessionId;

  @override
  void initState() {
    super.initState();
    _loadSessionId();
    _loadProfiles();
  }

  Future<void> _loadSessionId() async {
    final prefs = await SharedPreferences.getInstance();
    final existing = prefs.getString(_sessionIdKey);
    if (existing != null && existing.isNotEmpty) {
      setState(() => _sessionId = existing);
      return;
    }
    final generated = _generateSessionId();
    await prefs.setString(_sessionIdKey, generated);
    if (mounted) {
      setState(() => _sessionId = generated);
    }
  }

  String _generateSessionId() {
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));
    return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
  }

  Future<void> _loadProfiles() async {
    try {
      final profiles = await _api.listProfiles();
      setState(() {
        _profiles = profiles;
        _selectedVoiceId = profiles.isNotEmpty ? profiles.first.voiceId : null;
      });
    } catch (_) {}
  }

  Future<void> _createVoiceProfile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['wav', 'mp3', 'm4a', 'ogg'],
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;

    final sample = result.files.first;
    final name = _nameController.text.trim();
    if (name.isEmpty) return;

    setState(() => _isBusy = true);
    try {
      await _api.createVoiceProfile(
        name: name,
        sample: sample,
        transcriptHint: _hintController.text.trim(),
      );
      await _loadProfiles();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Perfil de voz creado.')),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error creando la voz: $error')),
        );
      }
    } finally {
      setState(() => _isBusy = false);
    }
  }

  Future<void> _sendAudio() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['wav', 'mp3', 'm4a', 'ogg'],
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;

    setState(() => _isBusy = true);
    try {
      final payload = await _api.sendAudioChat(
        audio: result.files.first,
        sessionId: _sessionId,
        voiceId: _selectedVoiceId,
      );
      setState(() {
        _lastTranscript = payload['transcript'] as String?;
        _lastAnswer = payload['answer'] as String?;
      });
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error procesando el audio: $error')),
        );
      }
    } finally {
      setState(() => _isBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ARIA Voz')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _nameController,
            decoration: const InputDecoration(
              labelText: 'Nombre del perfil de voz',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _hintController,
            minLines: 2,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Texto aproximado del audio de muestra',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _isBusy ? null : _createVoiceProfile,
            icon: const Icon(Icons.library_music_outlined),
            label: const Text('Crear perfil desde audio'),
          ),
          const SizedBox(height: 24),
          DropdownButtonFormField<String>(
            value: _selectedVoiceId,
            decoration: const InputDecoration(
              labelText: 'Perfil de voz activo',
              border: OutlineInputBorder(),
            ),
            items: _profiles
                .map(
                  (profile) => DropdownMenuItem(
                    value: profile.voiceId,
                    child: Text(profile.name),
                  ),
                )
                .toList(),
            onChanged: (value) {
              setState(() => _selectedVoiceId = value);
            },
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _isBusy ? null : _sendAudio,
            icon: const Icon(Icons.mic),
            label: const Text('Enviar audio a ARIA'),
          ),
          const SizedBox(height: 24),
          if (_lastTranscript != null) ...[
            Text('Transcripción', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(_lastTranscript!),
            const SizedBox(height: 16),
          ],
          if (_lastAnswer != null) ...[
            Text('Respuesta', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(_lastAnswer!),
          ],
          const SizedBox(height: 24),
          const Text(
            'Consejo: usa un audio limpio, sin música, de 30 a 60 segundos para clonar la voz con mejor calidad.',
          ),
        ],
      ),
    );
  }
}
