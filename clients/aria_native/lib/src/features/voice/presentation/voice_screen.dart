import 'package:audioplayers/audioplayers.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/models/chat_models.dart';
import '../../../core/services/aria_api.dart';
import '../../../core/services/session_id_service.dart';


class VoiceScreen extends StatefulWidget {
  const VoiceScreen({super.key});

  @override
  State<VoiceScreen> createState() => _VoiceScreenState();
}


class _VoiceScreenState extends State<VoiceScreen> {
  final _api = AriaApi();
  final _nameController = TextEditingController();
  final _hintController = TextEditingController();
  final _ttsTextController = TextEditingController();
  late final AudioPlayer _audioPlayer;

  List<VoiceProfile> _profiles = [];
  String? _selectedVoiceId;
  String? _lastTranscript;
  String? _lastAnswer;
  String? _lastSynthesizedAudioPath;
  bool _isBusy = false;
  bool _isSynthesizing = false;

  @override
  void initState() {
    super.initState();
    _audioPlayer = AudioPlayer();
    _loadProfiles();
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
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

    final service = Provider.of<SessionIdService>(context, listen: false);

    setState(() => _isBusy = true);
    try {
      final payload = await _api.sendAudioChat(
        audio: result.files.first,
        sessionId: service.sessionId,
        voiceId: _selectedVoiceId,
      );
      setState(() {
        _lastTranscript = payload['transcript'] as String?;
        _lastAnswer = payload['answer'] as String?;
        final synthPath = payload['synthesized_audio_path'] as String?;
        _lastSynthesizedAudioPath =
            synthPath != null && synthPath.isNotEmpty ? synthPath : null;
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

  Future<void> _synthesize() async {
    final text = _ttsTextController.text.trim();
    if (text.isEmpty) return;

    setState(() => _isSynthesizing = true);
    try {
      final response = await _api.synthesizeVoice(
        text: text,
        voiceId: _selectedVoiceId,
        language: 'es',
      );
      final outputPath = response['output_path'] as String?;
      if (outputPath != null && outputPath.isNotEmpty) {
        await _audioPlayer.play(DeviceFileSource(outputPath));
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Sintesis completada.')),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error sintetizando: $error')),
        );
      }
    } finally {
      setState(() => _isSynthesizing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final service = Provider.of<SessionIdService>(context, listen: true);

    return Scaffold(
      appBar: AppBar(
        title: const Text('ARIA Voz'),
        actions: [
          IconButton(
            tooltip: 'Nueva conversacion',
            onPressed: _isBusy
                ? null
                : () async {
                    await service.reset();
                    if (mounted) {
                      setState(() {
                        _lastTranscript = null;
                        _lastAnswer = null;
                        _lastSynthesizedAudioPath = null;
                      });
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Nueva conversacion iniciada.')),
                      );
                    }
                  },
            icon: const Icon(Icons.add_comment_outlined),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: TextField(
                    controller: _ttsTextController,
                    minLines: 1,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      labelText: 'Texto a sintetizar',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: ElevatedButton.icon(
                    onPressed: _isSynthesizing ? null : _synthesize,
                    icon: const Icon(Icons.record_voice_over),
                    label: Text(_isSynthesizing ? '...' : 'Sintetizar'),
                  ),
                ),
              ],
            ),
          ),
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
            Text('Transcripcion', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(_lastTranscript!),
            const SizedBox(height: 16),
          ],
          if (_lastAnswer != null) ...[
            Text('Respuesta', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(_lastAnswer!),
              subtitle: _lastSynthesizedAudioPath != null
                  ? const Text('Audio disponible')
                  : null,
              trailing: _lastSynthesizedAudioPath != null
                  ? IconButton(
                      icon: const Icon(Icons.play_arrow),
                      onPressed: () {
                        _audioPlayer.play(DeviceFileSource(_lastSynthesizedAudioPath!));
                      },
                      tooltip: 'Reproducir audio sintetizado',
                    )
                  : null,
            ),
          ],
          const SizedBox(height: 24),
          const Text(
            'Consejo: usa un audio limpio, sin musica, de 30 a 60 segundos para clonar la voz con mejor calidad.',
          ),
        ],
      ),
    );
  }
}
