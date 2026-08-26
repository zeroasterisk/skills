import SwiftUI

struct HoverInputsView: View {
    @State private var isHovering = false
    @State private var continuousHoverLocation: CGPoint = .zero
    
    var body: some View {
        VStack(spacing: 20) {
            // 1. Simple Hover State (Good for indicating interactivity)
            Text("Hover Over Me")
                .padding()
                .background(isHovering ? Color.blue.opacity(0.2) : Color.clear)
                .cornerRadius(8)
                .onHover { hovering in
                    // Update cursor or visual state
                    isHovering = hovering
                    if hovering {
                        NSCursor.pointingHand.push()
                    } else {
                        NSCursor.pop()
                    }
                }
            
            // 2. Continuous Hover (Good for high-precision tools, drawing, or custom controls)
            Rectangle()
                .fill(Color.secondary.opacity(0.1))
                .frame(width: 200, height: 200)
                .overlay(
                    Circle()
                        .fill(Color.red)
                        .frame(width: 10, height: 10)
                        .position(x: continuousHoverLocation.x, y: continuousHoverLocation.y)
                )
                .onContinuousHover { phase in
                    switch phase {
                    case .active(let location):
                        continuousHoverLocation = location
                    case .ended:
                        // Handle the end of hover (e.g. mouse left the view)
                        break
                    }
                }
        }
        .padding()
    }
}
