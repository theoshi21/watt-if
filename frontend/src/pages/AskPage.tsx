import { ChatPanel } from '../components/ChatPanel'

export default function AskPage() {
  return (
    // flex: 1 makes this div grow to fill whatever height the shell gives it
    // overflow: hidden keeps the page from growing taller than the viewport
    <div className="page-content ask-page-content" style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden', padding: '1.5rem' }}>
      <ChatPanel />
    </div>
  )
}
