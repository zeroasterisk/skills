import SwiftUI

@main
struct MenusApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .commands {
            // Replace standard Document commands if you have a custom structure,
            // or add custom application-specific commands here.
            
            CommandGroup(replacing: .newItem) {
                Button("New Workspace") {
                    createNewWorkspace()
                }
                .keyboardShortcut("n", modifiers: .command)
                
                Button("Open Workspace...") {
                    openWorkspace()
                }
                .keyboardShortcut("o", modifiers: .command)
            }
            
            CommandMenu("Action") {
                Button("Perform Magic") {
                    performMagic()
                }
                .keyboardShortcut("m", modifiers: [.command, .shift])
                
                Divider()
                
                Button("Reset State") {
                    resetState()
                }
                // Destructive or less common actions might not need shortcuts
                // but should still be in the menu
            }
        }
    }
    
    func createNewWorkspace() {}
    func openWorkspace() {}
    func performMagic() {}
    func resetState() {}
}

struct ContentView: View {
    var body: some View {
        Text("Right-click me!")
            .padding()
            // Provide contextual actions via right-click (Dock/in-app context)
            .contextMenu {
                Button("Copy Context") {
                    // copy action
                }
                Button("Share...") {
                    // share action
                }
            }
    }
}
