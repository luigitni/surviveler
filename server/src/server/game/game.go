package game

import (
	"fmt"
	"net"
	"os"
	"os/signal"
	"runtime"
	"server/core"
	"syscall"
	"time"
)

const (
	CONN_HOST        = ""
	CONN_PORT        = "1234"
	MAX_OUT_CHANNELS = 100
	MAX_IN_CHANNELS  = 100
)

type SurvCallback struct {
	Addr       net.Addr
	MsgFactory MsgFactory
}

func StartGameServer() {
	runtime.GOMAXPROCS(runtime.NumCPU())

	// creates a tcp listener
	tcpAddr, err := net.ResolveTCPAddr("tcp4", CONN_HOST+":"+CONN_PORT)
	FatalError(err, "Resolving addr")
	listener, err := net.ListenTCP("tcp", tcpAddr)
	FatalError(err, "Listening TCP")

	// creates a server
	config := &core.ServerCfg{
		MaxOutgoingChannels: MAX_OUT_CHANNELS,
		MaxIncomingChannels: MAX_IN_CHANNELS,
	}

	// creates the factory and register message types
	var survCB SurvCallback
	survCB.MsgFactory = *NewMsgFactory()
	survCB.MsgFactory.RegisterMsgType(PingId, PingMsg{})
	survCB.MsgFactory.RegisterMsgType(PongId, PongMsg{})
	survCB.MsgFactory.RegisterMsgType(PositionId, PositionMsg{})

	srv := core.NewServer(config, &survCB, &MsgReader{})

	// starts server (listening goroutine)
	go srv.Start(listener, time.Second)
	fmt.Println("listening:", listener.Addr())

	// catchs system signal
	chSig := make(chan os.Signal)
	signal.Notify(chSig, syscall.SIGINT, syscall.SIGTERM)
	fmt.Println("Signal: ", <-chSig)

	// stops server
	srv.Stop()
}

func (this *SurvCallback) OnConnect(c *core.Conn) bool {

	this.Addr = c.GetRawConn().RemoteAddr()
	fmt.Println("OnConnect:", this.Addr)

	// start a goroutine that spams client with player position!
	go func() {

		for {
			switch {
			case c.IsClosed():
				return
			default:

				// temporary: for now spam a position every 200ms
				msg, err := NewMessage(MsgType(PositionId), PositionMsg{7, 9})

				err = c.AsyncSendMessage(msg, time.Second)
				if err != nil {
					fmt.Printf("Error in AsyncSendMessage: %v\n", err)
					return
				}
				fmt.Println("Sent a PositionMsg")
				time.Sleep(200 * time.Millisecond)
			}
		}
	}()

	return true
}

func (this *SurvCallback) OnIncomingMsg(c *core.Conn, cm core.Message) bool {

	var msg *Message
	var ok bool
	if msg, ok = cm.(*Message); !ok {
		panic("type assertion")
	}

	switch msg.Type {
	case PingId:

		// handle ping

		// temporary: for now we do it here... but it will be handled in
		// registered handlers using observers/notifiers...
		fmt.Printf("Received Ping: %v\n", msg)
		iping, err := this.MsgFactory.DecodePayload(PingId, msg.Buffer)

		var ping PingMsg
		var ok bool
		if ping, ok = iping.(PingMsg); !ok {
			panic("type assertion")
		}
		fmt.Printf("Decoded Ping: %v\n", ping)

		// reply pong
		pong, err := NewMessage(MsgType(PongId), PongMsg{ping.Id, MakeTimestamp()})
		err = c.AsyncSendMessage(pong, time.Second)
		if err != nil {
			fmt.Printf("Error in AsyncSendMessage: %v\n", err)
			return false
		}
		fmt.Println("Sent a Pong")

	default:
		fmt.Printf("Unknown MsgType: %v\n", msg)
		return false
	}

	return true
}

func (this *SurvCallback) OnClose(c *core.Conn) {
	fmt.Printf("Connection closed: %v\n", c.GetRawConn().RemoteAddr())
}