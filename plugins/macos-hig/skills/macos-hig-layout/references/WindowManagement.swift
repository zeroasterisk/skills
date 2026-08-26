import SwiftUI

@main
struct MacOSApp: App {
    var body: some Scene {
        // Main Application Window
        WindowGroup("Main Workspace", id: "main") {
            ContentView()
                // Ensure a reasonable minimum size so the layout doesn't break
                .frame(minWidth: 600, minHeight: 400)
        }
        // Idiomatic macOS window styling: hidden title bar for unified toolbar look
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unified(showsTitle: false))
        // Define resizability constraints
        .windowResizability(.contentMinSize)
        // Set a default size for the first launch
        .defaultSize(width: 800, height: 600)
        
        // Auxiliary Window (e.g., for a specific tool or detail view)
        Window("Inspector", id: "inspector") {
            InspectorView()
                .frame(minWidth: 300, idealWidth: 300, maxWidth: 400,
                       minHeight: 500, idealHeight: 600)
        }
        .keyboardShortcut("i", modifiers: [.command, .option])
        .defaultPosition(.trailing)
        
        // Settings Window (Standard macOS preferences)
        Settings {
            SettingsView()
                .frame(width: 500, height: 400)
                // Settings windows shouldn't be resizable unless necessary
                .fixedSize()
        }
    }
}

struct ContentView: View {
    var body: some View {
        NavigationSplitView {
            Sidebar()
        } detail: {
            Text("Main Content Area")
        }
    }
}

struct InspectorView: View {
    var body: some View {
        Text("Inspector Controls")
    }
}

struct Sidebar: View {
    var body: some View {
        List {
            Text("Item 1")
            Text("Item 2")
        }
    }
}

struct SettingsView: View {
    var body: some View {
        Text("App Settings")
    }
}
