import 'package:flutter/material.dart';

import 'features/chat/presentation/chat_screen.dart';
import 'features/voice/presentation/voice_screen.dart';


class AriaApp extends StatelessWidget {
  const AriaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ARIA',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      home: const _AriaShell(),
    );
  }
}


class _AriaShell extends StatefulWidget {
  const _AriaShell();

  @override
  State<_AriaShell> createState() => _AriaShellState();
}


class _AriaShellState extends State<_AriaShell> {
  int _currentIndex = 0;

  final _pages = const [
    ChatScreen(),
    VoiceScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        destinations: const [
          NavigationDestination(icon: Icon(Icons.chat_bubble_outline), label: 'Chat'),
          NavigationDestination(icon: Icon(Icons.mic_none), label: 'Voz'),
        ],
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
      ),
    );
  }
}
