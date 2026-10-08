class ChatMessage {
  ChatMessage({
    required this.role,
    required this.content,
  });

  final String role;
  final String content;
}


class VoiceProfile {
  VoiceProfile({
    required this.voiceId,
    required this.name,
    required this.samplePath,
  });

  final String voiceId;
  final String name;
  final String samplePath;

  factory VoiceProfile.fromJson(Map<String, dynamic> json) {
    return VoiceProfile(
      voiceId: json['voice_id'] as String,
      name: json['name'] as String,
      samplePath: json['sample_path'] as String,
    );
  }
}
