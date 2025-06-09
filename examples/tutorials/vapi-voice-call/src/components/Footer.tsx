const Footer = () => {
  return (
    <footer className="bg-gray-900 text-white py-8">
      <div className="container-max">
        <div className="text-center">
          <h3 className="text-2xl font-bold mb-2 text-secondary">YellowFin Real Estate</h3>
          <p className="text-gray-400 mb-4">Your trusted Austin home buying specialists</p>
          <p className="text-sm text-gray-500">
            © {new Date().getFullYear()} YellowFin Real Estate. All rights reserved. | 
            Licensed Real Estate Broker in Texas
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
