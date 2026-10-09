import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/models/chat_models.dart';
import '../../../core/services/aria_api.dart';
import '../../../core/services/session_id_service.dart';


class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _api = AriaApi();
  final _controller = TextEditingController();
  final List<ChatMessage> _messages = [];
  bool _isSending = false;

  Future<void> _send() async {
    final prompt = _controller.text.trim();
    if (prompt.isEmpty || _isSending) return;

    final service = Provider.of<SessionIdService>(context, listen: false);

    setState(() {
      _isSending = true;
      _messages.add(ChatMessage(role: 'user', content: prompt));
      _controller.clear();
    });

    try {
      final answer = await _api.sendChat(prompt, sessionId: service.sessionId);
      setState(() {
        _messages.add(ChatMessage(role: 'assistant', content: answer));
      });
    } catch (error) {
      setState(() {
        _messages.add(ChatMessage(role: 'assistant', content: 'Error: $error'));
      });
    } finally {
      setState(() {
        _isSending = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final service = Provider.of<SessionIdService>(context, listen: true);

    return Scaffold(
      appBar: AppBar(
        title: const Text('ARIA Chat'),
        actions: [
          IconButton(
            tooltip: 'Nueva conversacion',
            onPressed: _isSending
                ? null
                : () async {
                    await service.reset();
                    if (mounted) {
                      setState(() {
                        _messages.clear();
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
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                final isUser = message.role == 'user';
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(12),
                    constraints: const BoxConstraints(maxWidth: 560),
                    decoration: BoxDecoration(
                      color: isUser
                          ? Theme.of(context).colorScheme.primaryContainer
                          : Theme.of(context).colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(message.content),
                  ),
                );
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    minLines: 1,
                    maxLines: 4,
                    decoration: const InputDecoration(
                      hintText: 'Pídele algo a ARIA...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton(
                  onPressed: _isSending ? null : _send,
                  child: Text(_isSending ? '...' : 'Enviar'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
