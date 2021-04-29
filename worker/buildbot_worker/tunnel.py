
from twisted.internet import defer
from twisted.internet import interfaces
from twisted.internet import protocol
from zope.interface import implementer


class HTTPTunnelClient(protocol.Protocol):

    def __init__(self, connectedDeferred):
        # this gets set once the tunnel is ready
        self._proxyWrappedProtocol = None
        self._connectedDeferred = connectedDeferred

    def connectionMade(self):
        request = "CONNECT {}:{} HTTP/1.1\r\n\r\n".format(
            self.factory.host, self.factory.port)
        self.transport.write(request.encode())

    def connectionLost(self, reason):
        if self._proxyWrappedProtocol:
            # Proxy connectionLost to the wrapped protocol
            return self._proxyWrappedProtocol.connectionLost(reason)

    def dataReceived(self, data):
        if self._proxyWrappedProtocol is not None:
            # If tunnel is already established, proxy dataReceived()
            # calls to the wrapped protocol
            return self._proxyWrappedProtocol.dataReceived(data)

        # process data from the proxy server
        _, status, _ = data.split(b"\r\n")[0].split(b" ", 2)
        if status != b"200":
            return self.transport.loseConnection()

        self._proxyWrappedProtocol = (
            self.factory._proxyWrappedFactory.buildProtocol(
                self.transport.getPeer()))
        self._proxyWrappedProtocol.makeConnection(self.transport)
        self._connectedDeferred.callback(self._proxyWrappedProtocol)

        # forward all trafic directly to the wrapped protocol
        self.transport.protocol = self._proxyWrappedProtocol


class HTTPTunnelFactory(protocol.ClientFactory):
    protocol = HTTPTunnelClient

    def __init__(self, host, port, wrappedFactory):
        self.host = host
        self.port = port

        self._proxyWrappedFactory = wrappedFactory
        self._onConnection = defer.Deferred()

    def doStart(self):
        super().doStart()
        # forward start notifications through to the wrapped factory.
        self._proxyWrappedFactory.doStart()

    def doStop(self):
        # forward stop notifications through to the wrapped factory.
        self._proxyWrappedFactory.doStop()
        super().doStop()

    def buildProtocol(self, addr):
        proto = self.protocol(self._onConnection)
        proto.factory = self
        return proto

    def clientConnectionFailed(self, connector, reason):
        if not self._onConnection.called:
            self._onConnection.errback(reason)


@implementer(interfaces.IStreamClientEndpoint)
class HTTPTunnelEndpoint(object):

    def __init__(self, host, port, proxyEndpoint):
        self.host = host
        self.port = port
        self.proxyEndpoint = proxyEndpoint

    def connect(self, protocolFactory):
        tunnel = HTTPTunnelFactory(self.host, self.port, protocolFactory)
        d = self.proxyEndpoint.connect(tunnel)
        # once tunnel connection is established,
        # defer the subsequent server connection
        d.addCallback(lambda result: tunnel._onConnection)
        return d
